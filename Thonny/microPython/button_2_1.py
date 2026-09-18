from machine import  Pin
import time

key = Pin(0, Pin.IN, Pin.PULL_UP)

try:
    while True:
        key_value = key.value()
        print(key_value)
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("코드를 종료합니다.")