# Picow A

This readme defines the use and lessons of the Raspberry Pico that I created.

### Intended Usage

Bedroom-located proximity, temperature and humidity sensor to link into home assistant for automation & monitoring.
To replace an existing Phillips Hue sensor so that can be re-purposed for another room. 

### Hardware

- Raspberry Pi pico W
- DHT20 Temperature & Humidity Sensor over I2C
- Red + Green LEDs
- HW-416 PIR Sensor
- Push button

### Lessons

The PIR sensor can seem to be affected something on the system, or by interference from the system. After soldering everything to a tight prototype board package it would toggle on/off repeatedly without motion. Adding distance between the sensor and pico package helped. Not sure on the exact cause. 

LEDs are always annoying at night, need to set these to optional (Toggle on/off via button?), especially if located within sleeping areas. Update: Added toggle of lights on button shortpress, defaults to on.

A soft-reset button would help to trigger restarts without messing with power cable/plug. Update: Now done via long-press. 

Button can be flaky, especially when pressing while touching other pins.

The temp sensor seems to read quite high, possibly gaining heat form the pico board/chip?

You can only have one `.irq` handler on a pin at a time, additional handlers will be ignored. Have need to combine triggers.

I used and async/await setup originally for easy handling of polling sensors with different poll times, to have each on their own mini event-based loops.
This worked but provides less control of the main thread and complicates things logically.
Reworked to a custom equivilent, where we find the soonest time for next sensor update then wait for that.
Tried to use `machine.lightsleep` but it would jam things up and required power cycle. I suspect could be due to keep-alives of WiFi and/or MQTT.
Could maybe only connect to those when required?