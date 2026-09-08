import time
from flask import Blueprint, Response, render_template, jsonify
from apps.services import yolo_detector

stream = Blueprint(
    "stream",
    __name__,
    template_folder="templates",
    static_folder="static",
)

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
            if yolo_detector.current_frame is not None:
                import cv2
                ret, buffer = cv2.imencode(".jpg", yolo_detector.current_frame)
                if ret:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            time.sleep(0.03)
    finally:
        yolo_detector.active_connections -= 1

@stream.route("/labels_feed")
def labels_feed():
    """마스터 엔진이 가공 중인 실시간 좌표 데이터를 상시 100% 무중단 리턴합니다."""
    return jsonify({"boxes": yolo_detector.current_boxes})

# apps/stream/views.py 하단 스위칭 라우터 수정 교체
@stream.route("/change_source/<source_key>")
def change_hybrid_source(source_key):
    """
    [마스터 통합 제어기] 동영상 1,2,3번 및 아두이노 실시간 드론 캠의 
    모든 물리 신호가 이 단 하나의 게이트웨이 함수로 집중 처리됩니다.
    """
    # 🎯 [오타 완치] 글자 사이사이에 끼어있던 유령 공백 스페이스를 완벽하게 제거했습니다.
    VIDEO_PATH_MAP = {
        "video_1": "C:/project_team3/workspaces/project_SSA/videos/streaming_0.mp4",
        "video_2": "C:/project_team3/workspaces/project_SSA/videos/streaming_1.mp4",
        "video_3": "C:/project_team3/workspaces/project_SSA/videos/streaming_2.mp4"
    }
    
    if source_key == "esp32":
        # 아두이노 기기 주소를 하이브리드 스트림으로 직결 주입
        esp32_url = "http://192.168.137.212:80/stream"
        yolo_detector.change_ai_source_runtime("esp32", esp32_url)
        return jsonify({"status": "SUCCESS", "mode": "esp32"})
        
    elif source_key in VIDEO_PATH_MAP:
        target_path = VIDEO_PATH_MAP[source_key]
        yolo_detector.change_ai_source_runtime("video", target_path)
        return jsonify({"status": "SUCCESS", "mode": source_key})
        
    return jsonify({"status": "FAIL", "message": f"Invalid Key: {source_key}"}), 400
