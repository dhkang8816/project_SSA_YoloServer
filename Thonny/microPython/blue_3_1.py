import bluetooth,ble_simple_peripheral,time

ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble,name='kang_123')

def on_rx(read):
    print("RX", read)
    
p.on_write(on_rx)