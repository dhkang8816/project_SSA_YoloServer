from machine import Pin
from machine import ADC
import time

cds_sensor=ADC(Pin(8))
cds_sensor.atten(ADC.ATTN_11DB)

LED_RED = Pin(21, Pin.OUT)
LED_GREEN = Pin(47, Pin.OUT)
LED_BLUE = Pin(48, Pin.OUT)

while True:
    cds_value = cds_sensor.read()
    print(cds_value)

    if cds_value < 500:
        LED_RED.on()
        LED_GREEN.on()
        LED_BLUE.on()
    else:
        LED_RED.off()
        LED_GREEN.off()
        LED_BLUE.off()

    time.sleep(0.5)