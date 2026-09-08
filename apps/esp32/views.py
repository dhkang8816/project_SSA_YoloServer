import threading
import time
import warnings
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from flask import Blueprint, Response, render_template, jsonify
import sys
import requests
import os

# 🎯 오라클 통신 서비스 및 YOLO 전역 엔진 완벽 연동
from apps.services import oracle_service
from apps.services import yolo_detector

warnings.filterwarnings("ignore", category=FutureWarning)
# 💡 스레드 함수 직전에 상태 감지용 플래그 전역 변수 하나 추가
has_resetted = False

esp32_yolov12 = Blueprint(
    "esp32_yolov12",
    __name__,
    template_folder="templates",
    static_folder="static",
)

ESP32_STREAM_URL = "http://192.168.137.212:80/stream"
esp32_current_frame = None 
esp32_boxes = [] 
is_running = True
esp_mode_active = False 
frame_lock = threading.Lock() 

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

@esp32_yolov12.route("/")
def index():
    oracle_service.fetch_target_counts()
    total_animal_count = sum(yolo_detector.TARGET_ANIMALS.values())
    danger_count = 0  
    animal_detect = 0
    return render_template(
        "esp32/index.html",
        animal_count=total_animal_count,
        danger_detect=danger_count,
        animal_detect=animal_detect
    )

# 🎯 [라벨 복구 핵심 교정 1] 자바 스프링의 모드 변경 신호를 받아 AI 전역 변수를 완전히 인터락 제어합니다.
@esp32_yolov12.route("/change_mode/<mode_name>")
def change_mode_signal(mode_name):
    global esp_mode_active, esp32_current_frame, esp32_boxes
    
    if mode_name == 'esp32':
        esp_mode_active = True
        
        # 💡 ESP32 구동 시 일반 동영상 YOLO 분석 백그라운드 연산을 멈춰서 자원 충돌을 방지합니다.
        yolo_detector.current_boxes = []
        print("[플라스크] 🚁 ESP32 드론 라이브 모드 가동 승인! 일반 동영상 라벨 큐 클리어.", file=sys.stderr)
        
    else:
        esp_mode_active = False
        with frame_lock:
            esp32_current_frame = None
            esp32_boxes = []
            
        # 💡 [버그 완치 포인트] 일반 동영상 모드로 돌아올 때, 동영상용 AI 엔진의 타이머와 
        # 감지 로직 안정화 대기 시간을 완전히 리셋해 주어 즉시 라벨을 그리도록 깨웁니다.
        yolo_detector.current_boxes = []
        yolo_detector.program_start_time = time.time() # 3초 로딩 대피선 강제 리셋 효과
        print("[플라스크] 🎬 로컬 동영상 채널 복귀 감지 -> yolo_detector 엔진 원격 기동 및 락 해제", file=sys.stderr)
        
    return jsonify({"status": "mode_changed"})

def esp32_video_stream_receiver():
    """백그라운드에서 무선 하드웨어 스트림을 수신해 YOLO 분석을 수행하는 엔진입니다."""
    global esp32_current_frame, esp32_boxes, is_running, esp_mode_active, has_resetted
    print("[스레드 가동] 하드웨어 무선 수신 백그라운드 엔진 기동.", file=sys.stderr)
    
    model = YOLO("C:/project_team3/workspaces/project_SSA/runs/detect/my_yolov12_project/yolov8n_train-6/weights/best.pt")
    cap = None
    
    while is_running:
        try:
            #  [라벨 복구 마법의 전원 스위치 개조 완료]
            if not esp_mode_active:
                if cap is not None:
                    try: cap.release()
                    except: pass
                    cap = None
                
                # ⭐ 0.5초마다 무한 리셋하는 버그 원천 차단! (전환 시 단 한 번만 실행되도록 보호)
                if not has_resetted:
                    import time
                    yolo_detector.program_start_time = time.time()
                    
                    # 안전하게 복구 주입 (딕셔너리가 살아있다면 내부 값만 리셋)
                    if hasattr(yolo_detector, 'under_target_start_time'):
                        yolo_detector.under_target_start_time = {"0": None, "1": None}
                        yolo_detector.recovery_start_time = {"0": None, "1": None}
                    
                    has_resetted = True # 🛡️ 한 번 리셋했으므로 다음 루프부턴 건너뜁니다.
                    print("[플라스크 백그라운드] 동영상 채널 타이머 최초 1회 초기화 완료.")
                
                time.sleep(0.5)
                continue
                
            # ESP32 모드가 켜지면 나중에 다시 동영상 모드로 갈 때 리셋할 수 있게 플래그를 풀어줍니다.
            has_resetted = False
            # ✅ 요청하신 정밀 정렬 괄호 튜플 주소 규격 완벽 사수
            if cap is None:
                full_url = (
                    "http://"
                    "192.168.137.212"
                    ":80"
                    "/stream"
                )
                print(f"[DEBUG] ESP32 OpenCV 비디오 캡처 연결 시도 -> {full_url}", file=sys.stderr)
                cap = cv2.VideoCapture(full_url)
            
            if not cap.isOpened():
                print("❌ [DEBUG] ESP32 카메라 스트림 열기 실패. 재시도 중...", file=sys.stderr)
                cap = None
                time.sleep(2)
                continue
            
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            success, frame = cap.read()
            if not success:
                print("⚠ [DEBUG] 프레임 읽기 실패. 스트림 재연결 프로세스 가동...", file=sys.stderr)
                if cap is not None:
                    try: cap.release()
                    except: pass
                    cap = None
                time.sleep(0.5)
                continue
            
            if frame is not None and isinstance(frame, np.ndarray) and len(frame.shape) == 3:
                results = model(frame, conf=0.5, verbose=False)
                temp_boxes = []
                
                if results and len(results) > 0 and results.boxes is not None:
                    boxes_obj = results.boxes
                    
                    detected_names = []
                    for box in boxes_obj:
                        cls_id = int(box.cls.item())
                        detected_names.append(model.names[cls_id])
                    
                    # 오라클 미달 감지 타이머 가동
                    yolo_detector.process_animal_detection_logic(detected_names)
                    
                    # 🎯 [2차원 대괄호 완벽 파괴 좌표 연산 규칙 적용]
                    for box in boxes_obj:
                        if box.conf is not None and len(box.conf) > 0 and box.conf.item() >= 0.50:
                            coords = box.xyxy.tolist()
                            if len(coords) > 0:
                                rx = coords
                                ry = coords
                                rw = coords - coords
                                rh = coords - coords
                                cls_id = int(box.cls.item())
                                label = model.names[cls_id]
                                score = float(box.conf.item())
                                temp_boxes.append([rx, ry, rw, rh, label, score])
                
                with frame_lock:
                    esp32_current_frame = frame.copy()
                    esp32_boxes = temp_boxes
            
            time.sleep(0.01)
            
        except Exception as e:
            print(f"❌ [스트림 통합 에러] 시스템 예외 발생: {e}", file=sys.stderr)
            if cap is not None:
                try: cap.release()
                except: pass
                cap = None
            time.sleep(1)


bg_thread = threading.Thread(target=esp32_video_stream_receiver, daemon=True)
bg_thread.start()

def generate_esp32_frames_bridge():
    global esp32_current_frame, esp_mode_active
    print("[스트리밍 게이트웨이] 브라우저가 ESP32 비디오 피드에 직접 연결됨.")
    
    while True:
        if esp_mode_active and esp32_current_frame is not None:
            local_frame = None
            with frame_lock:
                local_frame = esp32_current_frame.copy()
            
            if local_frame is not None:
                ret, buffer = cv2.imencode('.jpg', local_frame)
                if ret:
                    jpeg_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
            time.sleep(0.04) 
        else:
            time.sleep(0.1) 
            try:
                dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(dummy_img, "CONNECTING TO ESP32 CAM...", (120, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                _, dummy_buffer = cv2.imencode('.jpg', dummy_img)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + dummy_buffer.tobytes() + b'\r\n')
            except GeneratorExit:
                break
            except:
                pass

@esp32_yolov12.route('/video_feed')
def video_feed():
    return Response(generate_esp32_frames_bridge(), mimetype='multipart/x-mixed-replace; boundary=frame')

@esp32_yolov12.route('/labels_feed')
def labels_feed():
    global esp32_boxes
    with frame_lock:
        return jsonify({"boxes": esp32_boxes})
