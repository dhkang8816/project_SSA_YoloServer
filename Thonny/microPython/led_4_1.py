from machine import Pin
import time

LED_RED = Pin(21,Pin.OUT)

while True:
    LED_RED.value(1)
    time.sleep(1.0)
    LED_RED.value(0)
    time.sleep(1.0)