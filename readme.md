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