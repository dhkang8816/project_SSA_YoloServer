from machine import Pin, PWM
import time

# 6번 핀에 수동 부저(PWM) 설정
melody_buzzer = PWM(Pin(6, Pin.OUT))
melody_buzzer.duty(0)

# [상황 1] 유기 동물 부족 안내음 (차분한 2음절)
def play_animal_alert():
    melody_buzzer.freq(261)
    melody_buzzer.duty(5)  # 동물들을 위해 작은 볼륨
    time.sleep_ms(400)
    
    melody_buzzer.duty(0)
    time.sleep_ms(100)
    
    melody_buzzer.freq(329)
    melody_buzzer.duty(5)
    time.sleep_ms(600)
    
    melody_buzzer.duty(0)

# [상황 2] 이상 객체 감지 경고음 (빠른 사이렌 3회 반복)
def play_danger_alert():
    for _ in range(3):
        melody_buzzer.freq(600) # 고주파 날카로운 소리
        melody_buzzer.duty(5) # 최대 볼륨
        time.sleep_ms(150)
        
        melody_buzzer.freq(450)
        melody_buzzer.duty(5)
        time.sleep_ms(150)
        
    melody_buzzer.duty(0)