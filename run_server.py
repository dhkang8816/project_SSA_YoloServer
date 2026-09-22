"""Single-process production-style entry point for the Flask YOLO server.

Use this instead of ``flask run --debug`` while OpenCV/FFmpeg, COM6, or
background detection workers are active.  The reloader would create a second
process and can duplicate native resources.
"""

import os

from dotenv import load_dotenv

from apps.app import create_app


def _port():
    try:
        return int(os.getenv("FLASK_RUN_PORT", "5000"))
    except ValueError:
        return 5000


load_dotenv()
app = create_app("local")


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
        port=_port(),
        debug=False,
        use_reloader=False,
        threaded=True,
    )
