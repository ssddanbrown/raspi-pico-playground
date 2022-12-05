import machine
import utime
from libraries.hd44780 import HD44780

lcd_rs = machine.Pin(6, machine.Pin.OUT)
lcd_enable = machine.Pin(7, machine.Pin.OUT)
lcd_data4 = machine.Pin(8, machine.Pin.OUT)
lcd_data5 = machine.Pin(9, machine.Pin.OUT)
lcd_data6 = machine.Pin(10, machine.Pin.OUT)
lcd_data7 = machine.Pin(11, machine.Pin.OUT)

count = 0

while count < 500:
    lcd = HD44780(lcd_rs, lcd_enable, lcd_data4, lcd_data5, lcd_data6, lcd_data7)
    lcd.write("Hello there\n{} times".format(count))
    utime.sleep(1)
    count += 1
