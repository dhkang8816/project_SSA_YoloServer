import time

melody_buzzer = PWM(Pin(6, Pin.OUT), freq=100, duty=0)
melody_buzzer.duty(0)

MELODY = [392, 392, 440, 440, 392, 392, 330, 392, 392,
          330, 330, 293, 0, 392, 392, 440, 440, 392,
          392, 329, 392, 329, 293, 329, 261, 0]

try:
    while True:
        for note_freq in MELODY:
            if note_freq == 0:
                melody_buzzer.duty(0)
                time.sleep_ms(250)
            else:
                melody_buzzer.freq(int(note_freq))
                melody_buzzer.duty(512)
                time.sleep_ms(250)
                melody_buzzer.duty(0)
                time.sleep_ms(100)
except:
    melody_buzzer.duty(0)