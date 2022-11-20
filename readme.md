# Raspberry Pi Pico Playground

This is a personal playground for messing about with the Raspberry Pi Pico W.
This will contain my scripts and notes as I go.
Much of this will be messy and might not even work. I don't really know python either, and I'm bad at electronics. No details of wiring in here either, would need to assume based on pin usage. 

### Variables

Common variables and secrets should be within a `config.py` file. This will need to be uploaded to the Pico before running any scripts that depend on it. An example with all variables can be found in `config.example.py`.

### HomeAssistant & MQTT

Communication with HomeAssistant is done over MQTT. Here's a quick high-level reference of how this works:

- HomeAssistant has an official MQTT integration.
  - I used a built-in Mosquitto "broker".
- The broker is essentially the central server to send/receive messages.
  - In terms of data, It's like a smart pub/sub key => value store, where keys are called "Topics".
  - The tops seem to be viewed as a tree structure. 
  - [MQTT Explorer](http://mqtt-explorer.com/) is super useful to watch/browse this.
- From the pico, I send data directly into the broker.
  - It's on the same system as home assistant, just on different ports.
- HomeAssistant expects and will watch for certain key formats.
  -  A `homeassistant/binary_sensor/picow_a_proximity/config` topic will set the config for a `binary_sensor` ([home assistant term](https://www.home-assistant.io/integrations/binary_sensor.mqtt)) for an entity named `picow_a_proximity`. This config makes it automatically show in home assistant. 
    - This needs certain json, as per home assistant docs.
  - A separate topic, as defined in the config data, will handle the state/sensor-data. 

### Resources

- [Python Syntax](https://learnxinyminutes.com/docs/python/)
- MicroPython MQTT [docs](https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html) / [repo](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple)
- [Home Assistant MQTT Docs](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)
- [Useful video on power usage & modes](https://youtu.be/GqmnV_T4yAU?t=327)

### Components

##### DHT20 Temperature Sensor

- I2C address 0x38 (cannot be changed), 56 decimal
- 2.5V to 5.5V power and logic level
- Pin order from Left to Right (Looking at side with holes): Power, SDA, Ground, SCL
- Built in 4.7K I2C pullup resistors.
- Usage Humidity: 0... 100%RH
- Usage Temperature: -40ºC – 80ºC
- Typical accuracy of ±2% relative humidity, and ±0.3 °C at 20-80% RH and 20-60 °C
- Overall accuracy of ±3% relative humidity, and ±0.5 °C
- Temp conversion: t(°C) = (signal/2^20)*200-50
- Humidity conversion: rh% = (signal/2^20)*100


Added `ahtx0.py` file into this repo since I had issues downloading it as a library.
This does much of the heavily lifting since raw ic2 communication requires a back and forth conversation of bytes to initiate and request data for reading.