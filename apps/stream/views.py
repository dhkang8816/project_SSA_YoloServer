import time

import cv2
import numpy as np
from flask import Blueprint, Response, jsonify, render_template

from apps.services import yolo_detector


stream = Blueprint(
    "stream",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@stream.route("/")
def index():
    return render_template("index.html")


@stream.route("/video_feed")
def video_feed():
    """Backward-compatible stream for the selected/default source."""
    return _video_response(yolo_detector.get_default_source_key())


@stream.route("/video_feed/<source_key>")
def video_feed_by_source(source_key):
    if not yolo_detector.is_known_source(source_key):
        return jsonify({"error": "unknown source_key", "source_key": source_key}), 404
    return _video_response(source_key)


def _video_response(source_key):
    yolo_detector.start_source_worker(source_key)
    return Response(
        generate_frames(source_key),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def generate_frames(source_key=None):
    """Encode only the requested source's latest completed YOLO frame."""
    source_key = source_key or yolo_detector.get_default_source_key()
    yolo_detector.stream_client_opened()
    try:
        while True:
            frame = yolo_detector.get_latest_frame(source_key)
            if frame is None:
                frame = _waiting_frame(source_key)
            encoded, buffer = cv2.imencode(".jpg", frame)
            if encoded:
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes()
                    + b"\r\n"
                )
            time.sleep(0.03)
    finally:
        yolo_detector.stream_client_closed()


def _waiting_frame(source_key):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        f"CONNECTING: {source_key}",
        (120, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    return frame


@stream.route("/labels_feed")
def labels_feed():
    """Backward-compatible labels for the selected/default source."""
    return jsonify({"boxes": yolo_detector.get_latest_boxes()})


@stream.route("/labels_feed/<source_key>")
def labels_feed_by_source(source_key):
    if not yolo_detector.is_known_source(source_key):
        return jsonify({"error": "unknown source_key", "source_key": source_key}), 404
    return jsonify({"boxes": yolo_detector.get_latest_boxes(source_key)})


@stream.route("/status")
def source_status():
    """Expose per-source worker state for operational diagnostics."""
    return jsonify({
        "default_source": yolo_detector.get_default_source_key(),
        "sources": yolo_detector.get_source_status(),
    })


@stream.route("/change_source/<source_key>")
def change_hybrid_source(source_key):
    """Keep the old switch API but only change the default stream.

    All configured source workers keep running, so selecting one source no
    longer shuts down or replaces another source's detection pipeline.
    """
    if not yolo_detector.is_known_source(source_key):
        return jsonify({"status": "FAIL", "error": "unknown source_key", "source_key": source_key}), 404
    yolo_detector.set_default_source(source_key)
    return jsonify({"status": "SUCCESS", "mode": source_key})
