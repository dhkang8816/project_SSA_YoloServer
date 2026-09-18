from machine import Pin, PWM
import time

M1_motor = PWM(Pin(4), freq = 10000 ,duty=0)

try:
    while True:
        M1_motor.duty(0)
        print("0")
        time.sleep(2)
        
        M1_motor.duty(100)
        print("100")
        time.sleep(1)
        
        M1_motor.duty(200)
        print("200")
        time.sleep(2)
        
except KeyboardInterrupt:
    M1_motor.deinit()
    print("코드를 종료합니다.")