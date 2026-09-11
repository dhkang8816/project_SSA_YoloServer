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

# 🌟 [OpenCV 좀비 락 원천 폭파선]
# 파이썬 OpenCV 라이브러리의 밑단 네트워크 코어(FFmpeg)에 환경 변수를 강제 각인시킵니다.
# ESP32 기기가 꺼져서 패킷 지연이 1초(1000000 마이크로초)를 넘어가는 순간,
# 30초 동안 미련하게 대기하지 말고 즉시 "연결 실패(False)"를 뱉고 루프를 탈출하게 만듭니다.
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;1000000"
global_esp_cap = None
_capture_lock = threading.Lock()
_receiver_lock = threading.Lock()
_receiver_thread = None
_receiver_generation = 0

warnings.filterwarnings("ignore", category=FutureWarning)
# 💡 스레드 함수 직전에 상태 감지용 플래그 전역 변수 하나 추가
has_resetted = False

esp32_yolov12 = Blueprint(
    "esp32_yolov12",
    __name__,
    template_folder="templates",
    static_folder="static",
)

ESP32_STREAM_URL = "http://192.168.137.128:80/stream"
esp32_current_frame = None 
esp32_boxes = [] 
is_running = True
esp_mode_active = False 
frame_lock = threading.Lock() 

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

# =================================================================
# 🌟 [최종 완치 저격선] 비디오 전환 시 ESP32 로직 및 스레드 완전 박멸 가동
# =================================================================

@esp32_yolov12.route("/change_mode/<mode_name>")
def change_mode_signal(mode_name):
    global esp_mode_active, esp32_current_frame, esp32_boxes, has_resetted, global_esp_cap
    
    if mode_name == 'esp32':
        esp_mode_active = True
        has_resetted = False
        yolo_detector.current_boxes = []
        print("[플라스크]  ESP32 라이브 모드 가동! 스레드 출격.", file=sys.stderr)
        
        start_esp32_receiver()
        
    else:
        stop_esp32_receiver()
        # 🌟 [치트키 발동] 사용자가 비디오 모드로 탈출하면 플래그만 바꾸는 게 아니라,
        # 백그라운드 스레드가 갇혀있는 global_esp_cap 자원을 여기서 직접 release()로 부수어버립니다!
        esp_mode_active = False
        has_resetted = False
        
        try:
            if global_esp_cap is not None:
                global_esp_cap.release() # ➔ 30초 대기 중이던 OpenCV 소켓관을 밖에서 강제로 깨부숩니다.
                global_esp_cap = None
                print("💥 [강제 차단 완수] 외부에서 ESP32 VideoCapture 커넥션을 완전히 폭파했습니다.", file=sys.stderr)
        except Exception as e:
            print(f"⚠ 외부 파괴 도중 예외 방어: {e}", file=sys.stderr)
            
        with frame_lock:
            esp32_current_frame = None
            esp32_boxes = []
            
        yolo_detector.current_boxes = []
        yolo_detector.program_start_time = time.time()
        
    return jsonify({"status": "mode_changed"})


def _legacy_esp32_video_stream_receiver():
    """백그라운드에서 무선 하드웨어 스트림을 수신해 YOLO 분석을 수행하는 엔진"""
    global esp32_current_frame, esp32_boxes, is_running, esp_mode_active, has_resetted, global_esp_cap
    print("[스레드 가동] 🚀 하드웨어 무선 수신 백그라운드 엔진 기동.", file=sys.stderr)
    
    model = YOLO("C:/project_team3/workspaces/project_SSA/runs/detect/my_yolov12_project/yolov8n_train-6/weights/best.pt")
    full_url = ESP32_STREAM_URL
    
    # 윈도우 환경 최적화를 위해 주입했던 CAP_FFMPEG 복귀
    global_esp_cap = cv2.VideoCapture(full_url, cv2.CAP_FFMPEG)
    global_esp_cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000) # 1초 강제 타임아웃
    global_esp_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    while is_running and esp_mode_active:
        try:
            # 🌟 [최전방 방어선] 모드가 꺼지면 즉시 포트를 닫고 스레드 탈출 소멸
            if not esp_mode_active or not is_running:
                break
            
            if not global_esp_cap.isOpened():
                print("❌ [DEBUG] ESP32 카메라 스트림 열기 실패. 재시도 중...", file=sys.stderr)
                time.sleep(1.0)
                
                # 🌟 [재연결 진입 직전 방어선] 대기 시간 동안 모드가 바뀌었는지 재확인
                if not esp_mode_active or not is_running: break
                
                global_esp_cap = cv2.VideoCapture(full_url, cv2.CAP_FFMPEG)
                global_esp_cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)
                continue
            
            success, frame = global_esp_cap.read()
            if not success:
                print("⚠ [DEBUG] 프레임 읽기 실패. 스트림 재연결 프로세스 가동...", file=sys.stderr)
                if global_esp_cap is not None: global_esp_cap.release()
                time.sleep(0.5)
                
                if not esp_mode_active or not is_running: break
                
                global_esp_cap = cv2.VideoCapture(full_url, cv2.CAP_FFMPEG)
                global_esp_cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)
                continue
            
            # YOLO 추론 구간 (기존 로직 보존)
            if frame is not None and isinstance(frame, np.ndarray) and len(frame.shape) == 3:
                results = model(frame, conf=0.5, verbose=False)
                temp_boxes = []
                if results and len(results) > 0 and results.boxes is not None:
                    boxes_obj = results.boxes
                    detected_names = [model.names[int(box.cls.item())] for box in boxes_obj]
                    
                    yolo_detector.process_animal_detection_logic(detected_names, frame)
                    
                    for box in boxes_obj:
                        if box.conf is not None and box.conf.item() >= 0.50:
                            coords = box.xyxy.tolist()[0]
                            temp_boxes.append([coords[0], coords[1], coords[2]-coords[0], coords[3]-coords[1], model.names[int(box.cls.item())], float(box.conf.item())])
                    with frame_lock:
                        esp32_current_frame = frame.copy()
                        esp32_boxes = temp_boxes
            time.sleep(0.01)
            
        except Exception as e:
            print(f"❌ [스트림 통합 에러] 시스템 예외 발생: {e}", file=sys.stderr)
            if global_esp_cap is not None: 
                global_esp_cap.release()
            
            # 🌟 [핵심 버그 완치선] 예외 발생 후 재시도 루프를 돌기 직전, 
            # 모드가 꺼졌다면 미련하게 다시 찌르지 말고 즉시 break로 루프를 깨부숩니다!
            if not esp_mode_active or not is_running:
                break
            time.sleep(1.0)
            
    # 🌟 [최종 실링] while 루프를 탈출하면 안전하게 물리 포트를 release하고 스레드를 영구 증발 소멸시킵니다.
    print("🛑 [스레드 완전 증발] ESP32 카메라 소켓을 강제 해제하고 스레드를 영원히 매장합니다.", file=sys.stderr)
    if global_esp_cap is not None:
        global_esp_cap.release()
        global_esp_cap = None


# 🌟 [주의] 파일 맨 아래에 선언되어 있던 bg_thread.start() 자동 실행 구문은 
# 중복 가동 및 먹통 방지를 위해 과감하게 삭제하거나 주석 처리해 줍니다!
# bg_thread = threading.Thread(target=esp32_video_stream_receiver, daemon=True)
# bg_thread.start()

def _is_receiver_active(generation):
    return is_running and esp_mode_active and generation == _receiver_generation


def _wait_while_active(generation, seconds):
    """Make retry waits interruptible by a video-source change."""
    deadline = time.monotonic() + seconds
    while _is_receiver_active(generation) and time.monotonic() < deadline:
        time.sleep(0.05)


def _open_esp_capture():
    """Open one bounded FFMPEG connection to the HTTP MJPEG endpoint."""
    properties = (
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000,
    )
    try:
        cap = cv2.VideoCapture(ESP32_STREAM_URL, cv2.CAP_FFMPEG, properties)
    except (TypeError, cv2.error):
        # Older OpenCV builds do not support constructor properties. The FFMPEG
        # timeout environment option set above is still applied in that case.
        cap = cv2.VideoCapture(ESP32_STREAM_URL, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def stop_esp32_receiver():
    """Invalidate the receiver and release its socket immediately."""
    global is_running, esp_mode_active, _receiver_generation, global_esp_cap
    is_running = False
    esp_mode_active = False
    with _receiver_lock:
        _receiver_generation += 1
        receiver = _receiver_thread
    with _capture_lock:
        cap = global_esp_cap
        global_esp_cap = None
    if cap is not None:
        cap.release()
    # The FFMPEG open/read timeouts bound this wait. It prevents an immediate
    # video -> ESP32 switch from creating a second socket while the old worker
    # is still unwinding.
    if receiver is not None and receiver is not threading.current_thread():
        receiver.join(timeout=1.5)


def start_esp32_receiver():
    """Start at most one receiver. Repeated ESP32 clicks do not add threads."""
    global is_running, esp_mode_active, _receiver_generation, _receiver_thread
    with _receiver_lock:
        is_running = True
        esp_mode_active = True
        if _receiver_thread is not None and _receiver_thread.is_alive():
            return False
        _receiver_generation += 1
        generation = _receiver_generation
        _receiver_thread = threading.Thread(
            target=esp32_video_stream_receiver,
            args=(generation,),
            daemon=True,
            name="esp32-video-receiver",
        )
        _receiver_thread.start()
        return True


def esp32_video_stream_receiver(generation=None):
    """The sole ESP32 connection and YOLO consumer for one active generation."""
    global esp32_current_frame, esp32_boxes, global_esp_cap
    if generation is None:
        # Compatibility for any legacy direct call site.
        with _receiver_lock:
            generation = _receiver_generation

    model = YOLO("C:/project_team3/workspaces/project_SSA/runs/detect/my_yolov12_project/yolov8n_train-6/weights/best.pt")
    cap = None
    try:
        while _is_receiver_active(generation):
            cap = _open_esp_capture()
            with _capture_lock:
                if not _is_receiver_active(generation):
                    cap.release()
                    break
                global_esp_cap = cap

            if not cap.isOpened():
                cap.release()
                with _capture_lock:
                    if global_esp_cap is cap:
                        global_esp_cap = None
                _wait_while_active(generation, 1.0)
                continue

            while _is_receiver_active(generation):
                success, frame = cap.read()
                if not success:
                    break
                results = model(frame, conf=0.5, verbose=False)
                boxes = results[0].boxes if results else None
                detected_names = []
                temp_boxes = []
                if boxes is not None:
                    names = results[0].names
                    for box in boxes:
                        if box.conf.item() < 0.5:
                            continue
                        label = names[int(box.cls.item())]
                        detected_names.append(label)
                        coords = box.xyxy.tolist()[0]
                        temp_boxes.append([
                            coords[0], coords[1], coords[2] - coords[0],
                            coords[3] - coords[1], label, float(box.conf.item()),
                        ])
                yolo_detector.process_animal_detection_logic(detected_names, frame)
                with frame_lock:
                    esp32_current_frame = frame.copy()
                    esp32_boxes = temp_boxes

            cap.release()
            with _capture_lock:
                if global_esp_cap is cap:
                    global_esp_cap = None
            cap = None
            _wait_while_active(generation, 0.5)
    except Exception as e:
        print(f"[ESP32 receiver error] {e}", file=sys.stderr)
    finally:
        if cap is not None:
            cap.release()
        with _capture_lock:
            if global_esp_cap is cap:
                global_esp_cap = None
        if generation == _receiver_generation:
            with frame_lock:
                esp32_current_frame = None
                esp32_boxes = []


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
