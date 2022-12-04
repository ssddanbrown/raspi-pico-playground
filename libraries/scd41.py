"""
MicroPython driver for the SCD41 CO2, Temperature Sensor and Humidity Sensor

This was built using the micropython_ahtx0 driver by Andreas Bühl & Kattni Rembor as a guide:
https://github.com/targetblank/micropython_ahtx0
And was built following the datasheet at:
https://files.seeedstudio.com/wiki/Grove-CO2&Temperature&HumiditySensor-SCD4/res/Sensirion_CO2_Sensors_SCD4x_Datasheet.pdf

This driver can be used like so:
    thc_sda = machine.Pin(14)
    thc_scl = machine.Pin(15)
    i2c1 = machine.I2C(1, sda=thc_sda, scl=thc_scl, freq=100000)
    thc_sensor = SCD41(i2c1)
    print("co:", thc_sensor.carbon_dioxide, "temp:", thc_sensor.temperature, "rh:", thc_sensor.relative_humidity)

Requesting any of the values will initiate the sensor start its internal measurement cycle.
Sensor measurements are updated every 5s, although you can call request values sooner via your
class instance and the instance will:
  - Provide fresh results if the sensor has them ready.
  - Otherwise provide cached results if last fetched in the last 5s.
  - Otherwise wait until the sensor has new results to fetch.

The sensor requires a 1000ms power-on time. This driver assumes power-on at time of initiation.
If a reading is then requested, it will wait for the remainder time since initiation to ensure this time.
Between power-on and sensor-read delays, your first request of sensor data may cause a delay of up to ~6500ms.

While this sensor provides various interfaces for calibration and settings, this driver does not currently
provide methods for those.
"""
import utime


class SCD41:

    def __init__(self, i2c, address=0x62):
        self._i2c = i2c
        self._address = address
        self._buf = bytearray(9)
        self._readings = (0, 0, 0)  # co2, temp, rh
        self._last_readings_at = utime.ticks_add(utime.ticks_ms(), -10000)
        self._started_at = utime.ticks_ms()
        self._measuring = False

    def _initiate_measurement(self):
        """
        Initiate measurement polling with the sensor.
        Will presume the sensor was powered on when the instance was initiated and
        therefore wait the 1000ms time, required by the sensor, if that has not yet passed.
        We call 'stop_periodic_measurement' first as a form of soft-reset in the event the
        measurement mode is out of sync with this instance.
        """
        start_diff = utime.ticks_diff(utime.ticks_ms(), self._started_at)
        if start_diff < 1000:
            utime.sleep_ms(1001 - start_diff)

        self._stop_periodic_measurement()
        utime.sleep_ms(500)
        self._start_periodic_measurement()
        self._measuring = True

    def _start_periodic_measurement(self):
        """ Send the command to start periodic measurement """
        self._buf[0] = 0x21
        self._buf[1] = 0xb1
        self._i2c.writeto(self._address, self._buf[0:2])

    def _stop_periodic_measurement(self):
        """ Send the command to stop periodic measurement """
        self._buf[0] = 0x3f
        self._buf[1] = 0x86
        self._i2c.writeto(self._address, self._buf[0:2])

    def _read_measurement(self):
        """
        Send the command to read the current measurement, then store the result
        into the readings of this instance.
        The values stored are raw integer values from the sensor data.
        Reading from the sensor clears its measurement buffer, so this should only be called
        if there is data ready to be read.
        """
        self._buf[0] = 0xec
        self._buf[1] = 0x05
        self._i2c.writeto(self._address, self._buf[0:2])
        utime.sleep_ms(1)
        self._i2c.readfrom_into(self._address, self._buf)
        # Measure response is provided across 9 bytes like so:
        #  [2 co2 + 1 checksum] [2 temp + checksum] [2 rh + 1 checksum]
        self._readings = (
            self._buf[0] << 8 | self._buf[1],
            self._buf[3] << 8 | self._buf[4],
            self._buf[6] << 8 | self._buf[7],
        )
        self._last_readings_at = utime.ticks_ms()

    def _get_data_ready_status(self):
        """
        Send the command to check if the sensor has measurement data to be read.
        Handles the status response, where the sensor will indicate if the data
        is NOT ready by providing the least significant 11 bits as all zeroes.
        The result is formatted to a boolean for easy usage.
        """
        self._buf[0] = 0xe4
        self._buf[1] = 0xb8
        self._i2c.writeto(self._address, self._buf[0:2])
        utime.sleep_ms(1)
        self._i2c.readfrom_into(self._address, self._buf)
        return bool(((self._buf[0] << 8) | self._buf[1]) & 0x7FF)

    def _poll_reading(self):
        """
        Poll for a next reading.
        This will initiate measurement if it has not already started.
        If the sensor has data ready, we fetch it to get up-to-date readings.
        Otherwise, if the last sensor readings were recent (within the last 5s) then we
        consider the sensor polled and up-to-date already.
        Otherwise, we'll wait until the sensor has data ready and then read it once available.
        """
        if not self._measuring:
            self._initiate_measurement()

        ready = self._get_data_ready_status()
        if ready:
            self._read_measurement()
            return

        time_diff = utime.ticks_diff(utime.ticks_ms(), self._last_readings_at)
        if time_diff < 5000:
            return

        while not self._get_data_ready_status():
            utime.sleep_ms(100)

        self._read_measurement()

    def stop(self):
        """ Stops the sensor polling for measurements """
        self._stop_periodic_measurement()
        self._measuring = False

    @property
    def temperature(self):
        """ Get the temperature as a value in degrees centigrade """
        self._poll_reading()
        return (175 * (self._readings[1] / 65536)) - 45

    @property
    def relative_humidity(self):
        """ Get the relative humidity as a value in percent """
        self._poll_reading()
        return 100 * (self._readings[2] / 65536)

    @property
    def carbon_dioxide(self):
        """ Get the relative humidity as a value in ppm """
        self._poll_reading()
        return self._readings[0]
