# Picow B

This readme defines the use and lessons of the second Raspberry Pi Pico-W based device I created.

### Intended Usage

Living-located proximity, temperature, humidity and CO2 sensor to link into home assistant for automation & monitoring.

### Hardware

- Raspberry Pi pico W
- SCD41
- HW-416 PIR Sensor
- Push button
- Red + Green LEDs
- HD44780 based display
- Potentiometer for display brightness control.
- [2N2222](https://en.wikipedia.org/wiki/2N2222) Transistor to allow control of display LED

### Lessons

Become a lot more confident with binary-level operations from writing the sensor and display drivers for this. Also learnt the lower-level I2C work and the display serial-like communication methods.

On the display, the LED consumes a massive amount of power relative to everything else (incl. pico, excl. sensors) when powered on.


### Transistor Calculations

- LCD LED Current, 14.9mA @ 5v.
- Transistor base to emitter: ~1v
- GPIO control pin: 3.3v
- Target ~1mA to base
- 1v / 0.001mA = 1kOhm