import time
import cv2
import numpy as np
from flask import Blueprint, Response, render_template, jsonify
from apps.services import yolo_detector,oracle_service


stream = Blueprint(
    "stream",
    __name__,
    template_folder="templates",
    static_folder="static",
)

ESP32_STREAM_URL = "http://192.168.137.128:80/stream"

@stream.route("/")
def index():
    # yolo_detector.init_ai_metadata_from_oracle()
    return render_template("index.html")

@stream.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

def generate_frames():
    yolo_detector.active_connections += 1
    try:
        while True:
            # 1. YOLO 엔진이 정상적으로 프레임을 캐싱하고 있다면 해당 관제 영상 송출
            if yolo_detector.current_frame is not None:
                ret, buffer = cv2.imencode(".jpg", yolo_detector.current_frame)
                if ret:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + 
                           buffer.tobytes() + b"\r\n")
            
            # 2. 🌟 [30초 락 방멸 저격선] ESP32 미연결 등으로 영상이 없다면 가만히 멈춰 대기하지 않고,
            # 자바 톰캣(executeProxy)이 굳지 않도록 가상 대기 프레임을 0.03초마다 즉시 발사합니다!
            else:
                dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(dummy_img, "CONNECTING / NO STREAM FEED...", (120, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                ret, dummy_buffer = cv2.imencode(".jpg", dummy_img)
                if ret:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + 
                           dummy_buffer.tobytes() + b"\r\n")
            
            time.sleep(0.03) # 칼싱크 60ms 폭격 방어 주기 사수
    finally:
        yolo_detector.active_connections -= 1

@stream.route("/labels_feed")
def labels_feed():
    """마스터 엔진이 가공 중인 실시간 좌표 데이터를 상시 100% 무중단 리턴합니다."""
    return jsonify({"boxes": yolo_detector.current_boxes})

# =================================================================
# 🌟 [최종 완치 저격선] 비디오 전환 시 ESP32 무선 수신 스레드를 완전히 셧다운 시킵니다.
# =================================================================

@stream.route("/change_source/<source_key>")
def change_hybrid_source(source_key):
    """
    [마스터 통합 제어기] 동영상 1,2,3번 및 ESP32 드론 캠 스위칭 허브 (동적 드론 매핑 완치 버전)
    """
    VIDEO_PATH_MAP = {
        "video_1" : "C:/project_team3/workspaces/project_SSA/videos/streaming_0.mp4",
        "video_2" : "C:/project_team3/workspaces/project_SSA/videos/streaming_1.mp4",
        "video_3" : "C:/project_team3/workspaces/project_SSA/videos/streaming_2.mp4"
    }
    
    # ================================================================
    # ★ [버그 완치 핵심 주입선] 파이썬 서비스 파일의 전역 변수를 실시간 갱신합니다.
    # 사용자가 누른 실제 비디오 소스 키('video_1', 'video_2', 'esp32' 등)가 그대로 박힙니다.
    # ================================================================
    oracle_service.CURRENT_ACTIVE_SOURCE = str(source_key)
    print(f"✈ [채널 연동 완수] 실시간 분석 대상 비디오 소스 갱신: {oracle_service.CURRENT_ACTIVE_SOURCE}")

    #  [기존 복구 조치] 사용자가 일반 동영상 채널(video_1, 2, 3)로 탈출하려는 순간!
    if source_key in VIDEO_PATH_MAP or source_key != "esp32":
        # 1. 다른 파일에 분리되어 있던 esp32 수신 모듈의 러닝 스위치를 강제로 False로 꺼버립니다.
        from apps.esp32 import views as esp32_views
        esp32_views.stop_esp32_receiver()
        
        # 2. 혹시 기존에 물려있던 프레임 버퍼가 남아있다면 깨끗하게 공백 청소
        yolo_detector.current_boxes = []
        if hasattr(esp32_views, 'esp32_current_frame'):
            esp32_views.esp32_current_frame = None
            
        print(" [하이브리드 제어] 일반 동영상 전환 확인 ➔ ESP32 백그라운드 스레드 강제 셧다운 완료!")
        
        # 3. 안전하게 기존 로컬 동영상 재생 엔진 기동
        target_path = VIDEO_PATH_MAP.get(source_key, VIDEO_PATH_MAP["video_1"])
        yolo_detector.change_ai_source_runtime("video", target_path)
        return jsonify({"status": "SUCCESS", "mode": source_key})
        
    #  사용자가 실시간 드론 CAM (esp32)을 선택했을 때
    elif source_key == "esp32":
        from apps.esp32 import views as esp32_views
        
        # 스레드 전원 스위치를 다시 싱싱하게 켜줍니다.
        esp32_views.has_resetted = False
        
        # 아두이노 기기 주소를 하이브리드 스트림으로 직결 주입
        yolo_detector.change_ai_source_runtime("esp32", None)
        
        #  [스레드 부활] 꺼져있던 스레드를 이 창구에서 직접 안전하게 새로 깨워서 출격시킵니다.
        esp32_views.start_esp32_receiver()
        
        return jsonify({"status": "SUCCESS", "mode": "esp32"})
