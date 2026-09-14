"""Non-secret runtime settings with defaults that preserve the prototype setup."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _text(name, default):
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _float(name, default, minimum=0.0):
    try:
        value = float(_text(name, str(default)))
    except ValueError:
        return default
    return value if value >= minimum else default


def _int(name, default, minimum=0):
    try:
        value = int(_text(name, str(default)))
    except ValueError:
        return default
    return value if value >= minimum else default


SPRING_HOST = _text("SSA_SPRING_HOST", "http://localhost:80/project_ssa_spring")
ESP32_STREAM_URL = _text("SSA_ESP32_STREAM_URL", "http://192.168.137.128:80/stream")
YOLO_MODEL_PATH = _text(
    "SSA_YOLO_MODEL_PATH",
    str(PROJECT_ROOT / "runs" / "detect" / "my_yolov12_project" / "yolov8n_train-6" / "weights" / "best.pt"),
)
VIDEO_PATHS = {
    "video_1": _text("SSA_VIDEO_1_PATH", str(PROJECT_ROOT / "videos" / "streaming_0.mp4")),
    "video_2": _text("SSA_VIDEO_2_PATH", str(PROJECT_ROOT / "videos" / "streaming_1.mp4")),
    "video_3": _text("SSA_VIDEO_3_PATH", str(PROJECT_ROOT / "videos" / "streaming_2.mp4")),
}
UPLOAD_ROOT = _text("SSA_UPLOAD_ROOT", "C:/upload")

YOLO_CONFIDENCE = _float("SSA_YOLO_CONFIDENCE", 0.50, minimum=0.0)
ANIMAL_UNDER_TARGET_SECONDS = _float("SSA_ANIMAL_UNDER_TARGET_SECONDS", 10.0, minimum=0.0)
ANIMAL_RECOVERY_SECONDS = _float("SSA_ANIMAL_RECOVERY_SECONDS", 2.5, minimum=0.0)
ALARM_COOLDOWN_SECONDS = _float("SSA_ALARM_COOLDOWN_SECONDS", 10.0, minimum=0.0)
METADATA_REQUEST_TIMEOUT_SECONDS = _float("SSA_METADATA_REQUEST_TIMEOUT_SECONDS", 1.0, minimum=0.1)
EVENT_REQUEST_TIMEOUT_SECONDS = _float("SSA_EVENT_REQUEST_TIMEOUT_SECONDS", 3.0, minimum=0.1)
MAPPING_REQUEST_TIMEOUT_SECONDS = _float("SSA_MAPPING_REQUEST_TIMEOUT_SECONDS", 1.0, minimum=0.1)
ESP32_CAPTURE_TIMEOUT_MS = _int("SSA_ESP32_CAPTURE_TIMEOUT_MS", 1000, minimum=1)
ESP32_RECEIVER_JOIN_TIMEOUT_SECONDS = _float("SSA_ESP32_RECEIVER_JOIN_TIMEOUT_SECONDS", 1.5, minimum=0.1)
