from machine import Pin
import time

key1 = Pin(38, Pin.IN, Pin.PULL_UP)
prev_state1 = key1.value()
key2 = Pin(39, Pin.IN, Pin.PULL_UP)
prev_state2 = key2.value()

LED_RED = Pin(21, Pin.OUT)
LED_GREEN = Pin(47, Pin.OUT)
LED_BLUE = Pin(48, Pin.OUT)

state = 0
key_flag = 0

LED_RED.value(1)
LED_GREEN.value(0)
LED_BLUE.value(0)

def get_key1():
    global prev_state1
    current_state = key1.value()
    if current_state != prev_state1:
        prev_state = current_state
        if current_state == 0:
            return 1
    else:
         return 0
        
def get_key2():
    global prev_state2
    current_state = key2.value()
    if current_state != prev_state2:
        prev_state2 = current_state
        if current_state == 0:
            return 1
    else:
         return 0
        
while True:
    if get_key1():
        key_flag = 1
        if state > 0:
            state = state - 1
        print(state)
        time.sleep(0.1)
        
    if get_key2():
        key_flag = 1
        if state < 2:
            state = state + 1
        print(state)
        time.sleep(0.1)
        
    if key_flag == 1:
        key_flag = 0
        if state == 0:
            LED_RED.value(1)
            LED_GREEN.value(0)
            LED_BLUE.value(0)
        elif state == 1:
            LED_RED.value(0)
            LED_GREEN.value(1)
            LED_BLUE.value(0)
        elif state == 2:
            LED_RED.value(0)
            LED_GREEN.value(0)
            LED_BLUE.value(1)
