"""Background ESP32 environment-sensor polling and collision classification."""

import json
import math
import threading
import time

from apps.services import buzzer_helper


SENSOR_POLL_SECONDS = 1.0
# Must match the ESP32's validated ultrasonic range and collision thresholds.
MIN_VALID_DISTANCE_CM = 2.0
MAX_VALID_DISTANCE_CM = 50.0
COLLISION_CAUTION_CM = 30.0
COLLISION_WARNING_CM = 20.0
COLLISION_DANGER_CM = 10.0

_sensor_lock = threading.Lock()
_sensor_thread = None
_latest_status = {
    "temperature": 0,
    "humidity": 0,
    "illumination": 0,
    "distance": 0,
    "collisionWarning": False,
    "collisionLevel": "UNKNOWN",
    "sensorOnline": False,
}


def _collision_level(distance):
    # Zero is the explicit invalid/timeout value, never a 0cm collision.
    if (
        distance is None
        or not math.isfinite(distance)
        or not MIN_VALID_DISTANCE_CM <= distance <= MAX_VALID_DISTANCE_CM
    ):
        return "UNKNOWN"
    if distance < COLLISION_DANGER_CM:
        return "DANGER"
    if distance < COLLISION_WARNING_CM:
        return "WARNING"
    if distance < COLLISION_CAUTION_CM:
        return "CAUTION"
    return "SAFE"


def _numeric_value(payload, key):
    value = payload.get(key)
    if value is None:
        return 0
    try:
        value = float(value)
        return value if math.isfinite(value) else 0
    except (TypeError, ValueError):
        return 0


def _parse_sensor_output(output):
    """Read the final JSON object even if mpremote emits informational text."""
    for line in reversed((output or "").splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise ValueError("ESP32 sensor response did not contain JSON")


def _read_from_esp32():
    command = (
        'mpremote connect COM6 resume exec "import main, ujson; '
        'print(ujson.dumps(main.read_sensor_status()))"'
    )
    completed = buzzer_helper.run_mpremote(command, timeout=5, capture_output=True)
    payload = _parse_sensor_output(completed.stdout)
    return {
        "temperature": _numeric_value(payload, "temperature"),
        "humidity": _numeric_value(payload, "humidity"),
        "illumination": _numeric_value(payload, "illumination"),
        "distance": _numeric_value(payload, "distance"),
    }


def _offline_status():
    return {
        "temperature": 0,
        "humidity": 0,
        "illumination": 0,
        "distance": 0,
        "collisionWarning": False,
        "collisionLevel": "UNKNOWN",
        "sensorOnline": False,
    }


def _update_status():
    try:
        values = _read_from_esp32()
        level = _collision_level(values["distance"])
        status = {
            **values,
            "collisionWarning": level in {"CAUTION", "WARNING", "DANGER"},
            "collisionLevel": level,
            "sensorOnline": True,
        }
        if level in {"CAUTION", "WARNING", "DANGER"}:
            buzzer_helper.set_collision_level(level)
            pass
        else:
            buzzer_helper.set_collision_level("SAFE")
            pass
    except Exception as error:
        stderr = getattr(error, "stderr", None)
        detail = stderr.strip() if isinstance(stderr, str) and stderr.strip() else str(error)
        print(f"[sensor] ESP32 sensor read failed: {detail}")
        status = _offline_status()
        buzzer_helper.set_collision_level("SAFE")

    with _sensor_lock:
        _latest_status.update(status)


def _sensor_worker():
    while True:
        _update_status()
        time.sleep(SENSOR_POLL_SECONDS)


def start_sensor_service():
    """Start one non-blocking polling worker for the entire Flask process."""
    global _sensor_thread
    with _sensor_lock:
        if _sensor_thread is not None and _sensor_thread.is_alive():
            return False
        _sensor_thread = threading.Thread(
            target=_sensor_worker,
            name="esp32-sensor-worker",
            daemon=True,
        )
        _sensor_thread.start()
        print("[sensor] service worker started")
        return True


def get_latest_sensor_status():
    """Return the cache only; web requests never initiate ESP32 I/O."""
    with _sensor_lock:
        return dict(_latest_status)
