"""Application service bootstrap helpers."""

from apps.services.buzzer_helper import start_buzzer_service, stop_buzzer_service
from apps.services.notifier import start_notification_service, stop_notification_service
from apps.services.sensor_helper import start_sensor_service, stop_sensor_service


def start_services():
    """Initialize background services without emitting a test alarm."""
    print("[starter] services starting")
    start_buzzer_service()
    start_sensor_service()
    start_notification_service()
    print("[starter] services ready")


def stop_services():
    """Stop optional background services during Flask process shutdown."""
    stop_notification_service()
    stop_sensor_service()
    stop_buzzer_service()
