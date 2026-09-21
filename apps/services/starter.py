"""Application service bootstrap helpers."""

from apps.services.buzzer_helper import start_buzzer_service
from apps.services.sensor_helper import start_sensor_service


def start_services():
    """Initialize background services without emitting a test alarm."""
    start_buzzer_service()
    start_sensor_service()
