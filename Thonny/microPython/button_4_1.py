from machine import Pin
import time

key1=Pin(38,Pin.IN,Pin.PULL_UP)

while True:
    print(key1.value())
    time.sleep(0.1)