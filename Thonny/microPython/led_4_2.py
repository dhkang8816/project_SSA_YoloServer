from machine import Pin
import time

LED_RED = Pin(21,Pin.OUT)
LED_GREEN = Pin(47,Pin.OUT)
LED_BLUE = Pin(48,Pin.OUT)

while True:
    LED_RED.value(1)
    LED_GREEN.value(0)
    LED_BLUE.value(0)
    time.sleep(1.0)

    LED_RED.value(0)
    LED_GREEN.value(1)
    LED_BLUE.value(0)
    time.sleep(1.0)

    LED_RED.value(0)
    LED_GREEN.value(0)
    LED_BLUE.value(1)
    time.sleep(1.0)