from machine import Pin
import time
import dht
from machine import SoftI2C
from ssd1306 import SSD1306_I2C

dht11=dht.DHT11(Pin(18))

i2c = SoftI2C(sda=Pin(43), scl=Pin(44))
oled = SSD1306_I2C(128, 64, i2c)

try :
    while True:
        dht11.measure()
        temp = dht11.temperature()
        humi = dht11.humidity()
        if (temp == None) or (humi == None):
            print("센서 에러")
        else:
            print(f"온도:{temp}°C  습도:{humi}RH")
            
        oled.fill(0)
        oled.text("temp:"+str(temp)+"c",10,10)
        oled.text("humi:"+str(humi)+"%",10,20)
        oled.show()
        time.sleep(1.0)
        
except :
    pass