import machine
import utime
from libraries.scd41 import SCD41

thc_sda = machine.Pin(14)
thc_scl = machine.Pin(15)

# Busses & Wrapped Sensors
i2c1 = machine.I2C(1, sda=thc_sda, scl=thc_scl, freq=100000)

thc_sensor = SCD41(i2c1)
counter = 0
while True:
    utime.sleep(1)
    print("co:", thc_sensor.carbon_dioxide, "temp:", thc_sensor.temperature, "rh:", thc_sensor.relative_humidity,
          "count:", counter)
    counter += 1

# thc_sensor.stop()