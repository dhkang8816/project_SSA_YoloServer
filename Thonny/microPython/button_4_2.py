from machine import Pin
import time

key1=Pin(38,Pin.IN,Pin.PULL_UP)
prev_state = key1.value()

while True:
    current_state = key1.value()
    if current_state != prev_state:
        prev_state = current_state
        if current_state == 0:
            print("click")
        time.sleep(0.1)
