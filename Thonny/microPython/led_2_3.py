from machine import Pin
import time

green_led = Pin(42,Pin.OUT)

try:
    while True:
        green_led.off()
        time.sleep(1.0)
        green_led.on()
        time.sleep(1.0)

except KeyboardInterrupt:
    green_led.off()
    print("코드를 종료합니다.")