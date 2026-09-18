import bluetooth,ble_simple_peripheral, time

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name="kang_123")

def on_rx(read):
    
    print("="*50)
    for i in range(len(read)):
        print(i,read[i])
    print("="*50)
    
p.on_write(on_rx)