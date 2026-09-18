import bluetooth,ble_simple_peripheral, time

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name="kang_123")

def on_rx(read):
    
    control_data = [None] * 4
    for i in range(4):
        control_data[i] = read[i+1] - 100
    print("="*50)
    print("rol:",control_data[0])
    print("pit:",control_data[1])
    print("yaw:",control_data[2])
    print("thr:",control_data[3])
    
    if read[5] == 136:
        print('stop')
    elif read[5] == 24:
        print('take_off')
    elif read[5] == 72:
        print('landing')
    elif read[5] == 40:
        print('calibration')
    elif read[5] == 1:
        print('button1')
    elif read[5] == 2:
        print('button2')
    elif read[5] == 3:
        print('button3')
    elif read[5] == 4:
        print('button4')

p.on_write(on_rx)
            
        