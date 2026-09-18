from machine import Pin
import time

key1=Pin(38,Pin.IN,Pin.PULL_UP)
prev_state = key1.value()

def get_key1():
    global prev_state
    current_state = key1.value()
    if current_state != prev_state:
        prev_state = current_state
        if current_state == 0:
            return 1
    else:
         return 0
            
while True:
    if get_key1():
        print("click")
        time.sleep(0.1)
