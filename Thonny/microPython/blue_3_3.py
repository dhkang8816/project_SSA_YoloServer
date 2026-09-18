import bluetooth,ble_simple_peripheral, time

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name="kang_123")

def on_rx(read):
    
    control_data = [None] * 4
    
    print("="*50)
    for i in range(len(read)):
        print(i.read[i])
    print("="*50)
    
    for i in range(4):
        control_data[i] = read[i+1] - 100
        
    print('control:',control_data)

p.on_write(on_rx)