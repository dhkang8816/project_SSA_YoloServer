from machine import Pin
from machine import ADC
import time

cds_sensor=ADC(Pin(8))
cds_sensor.atten(ADC.ATTN_11DB)

while True:
    cds_value = cds_sensor.read()
    print(cds_value)
    time.sleep(0.5)