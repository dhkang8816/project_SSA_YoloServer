from machine import Pin
import time
from machine import SoftI2C
from ssd1306 import SSD1306_I2C

i2c = SoftI2C(sda=Pin(43), scl=Pin(44))
oled = SSD1306_I2C(128, 64, i2c)

oled.text("hi pyDrone",20,30)
oled.show()