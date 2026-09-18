from machine import Pin, PWM
import time

melody_buzzer = PWM(Pin(6, Pin.OUT), freq=100, duty=0)
melody_buzzer.duty(0)

frequency_list = [261, 293, 329, 349, 392, 440, 493, 523]

try:
    while True:
        for frequency in frequency_list:
            melody_buzzer.duty(512)
            melody_buzzer.freq(int(frequency))
            time.sleep_ms(500)
except:
    melody_buzzer.duty(0)