import bluetooth,ble_simple_peripheral,time
from machine import Pin
import drone
# 4번째 줄에 추가할 코드
ble = bluetooth.BLE()
ble.active(False)  # 기존 블루투스 신호를 강제로 끄기

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name='kang_0000')

d = drone.DRONE(flightmode = 1,debug = 0)

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
        
def on_rx(read):
    
    control_data = [None] * 4
    for i in range(4):
        control_data[i] = read[i+1] - 100
    
    d.control(rol = control_data[0], pit = control_data[1]+5, yaw = control_data[2], thr = control_data[3])
    
    if read[5] == 136:
        print('stop')
        d.stop()
    elif read[5] == 24:
        print('take_off')
        d.take_off(distance = 80)
    elif read[5] == 72:
        print('landing')
        d.landing()
    elif read[5] == 40:
        print('calibration')
        do_calibration()
    elif read[5] == 1:
        print('button1')
    elif read[5] == 2:
        print('button2')
    elif read[5] == 3:
        print('button3')
    elif read[5] == 4:
        print('button4')

do_calibration()
p.on_write(on_rx)
