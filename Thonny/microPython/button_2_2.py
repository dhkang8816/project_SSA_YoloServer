from machine import  Pin
import time

key = Pin(0, Pin.IN, Pin.PULL_UP)
prev_key = key.value()

try:
    while True:
        curr_key = key.value()
        if curr_key != prev_key:
            prev_key = curr_key
            if curr_key == 0:
                print("버튼 눌림",curr_key)
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("코드를 종료합니다.")