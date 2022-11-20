import machine
import ahtx0
import time

th_sda = machine.Pin(16)
th_scl = machine.Pin(17)
g_led = machine.Pin(0, machine.Pin.OUT)
r_led = machine.Pin(2, machine.Pin.OUT)

th_i2c = machine.I2C(0, sda=th_sda, scl=th_scl, freq=400000)
th_sensor = ahtx0.AHT10(th_i2c)


while True:
    temp = th_sensor.temperature
    rh = th_sensor.relative_humidity
    r_led.value(temp >= 20)
    g_led.value(rh >= 60)
    print("\nTemperature: %0.2f C" % temp)
    print("Humidity: %0.2f %%" % rh)
    time.sleep(1)
    