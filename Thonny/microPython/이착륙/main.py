import bluetooth,ble_simple_peripheral,time
from machine import Pin
import drone

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name='kang_123')

d = drone.DRONE(flightmode = 1,debug = 0)

key = Pin(0, Pin.IN, Pin.PULL_UP)
prev_key = key.value()

def do_calibration():
    green_led = Pin(42,Pin.OUT)
    while True:
        print(d.read_cal_data())
        if d.read_calibrated():
            print(d.read_cal_data())
            green_led.off()
            break
        green_led.on()
        time.sleep_ms(50)
        green_led.off()
        time.sleep_ms(50)

def get_key():
    global  prev_key
    curr_key = key.value()
    if curr_key != prev_key:
        prev_key = curr_key
        if curr_key == 0:
            return True
        time.sleep(0.1)
        
    return False

do_calibration()

try:
    while True:
        if get_key() == True:
            #버튼을 누르면 3초동안 대기
            for i in range(3 * 20):
                d.control(rol = 0, pit = 0, yaw = 0, thr = 0)
                time.sleep_ms(50)
            
            #이륙 5초동안 
            for i in range(3 * 20):
                d.control(rol = 0, pit = 0, yaw = 0, thr = 0)
                d.take_off(distance = 120)
                time.sleep_ms(50)
            
            #착륙하기 5초동안
            for i in range(3 * 20):
                d.control(rol = 0, pit = 0, yaw = 0, thr = 0)
                time.sleep_ms(50)
            
except KeyboardInterrupt:
    print("코드를 종료합니다.")
