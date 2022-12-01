# Raspberry Pi Pico Playground

This is a personal playground for messing about with the Raspberry Pi Pico W.
This will contain my scripts and notes as I go.
Much of this will be messy and might not even work. I don't really know python either, and I'm bad at electronics. No details of wiring in here either, would need to assume based on pin usage. 

Devices built have their own folders with their current script state, and readme to document that specific device.

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

### Connecting & Files

- The pico will it's `main.py` script as soon as it gets power.
- Can use `minicom -o -D /dev/ttyACM0` to open up a terminal into the MicroPython environment directly on the pi.
- [Rshell](https://github.com/dhylands/rshell) seems to provide a higher-level interface:
  - Connect with `rshell --buffer-size=512 -p /dev/ttyACM0`
  - Once connected, list out boards via `boards`. Seems to be called `pyboard`.
  - File operations then done by name like `ls /pyboard`.
  - Can get to REPL via `repl` command; Exit via `Ctrl+X`.

You can use rshell to upload, and run a file in a REPL (To see output) like so:

```shell
rshell --buffer-size=512 --quiet -p /dev/ttyACM0 "cp file.py /pyboard/dev.py; repl ~ import dev"
# Use Ctrl+X to exit
```

For uploading a file for normal usage, you can use:

```shell
rshell --buffer-size=512 --quiet -p /dev/ttyACM0 "cp file.py /pyboard/main.py; repl ~ import machine ~ machine.reset() ~"
```

I tried to get the above integrated with PyCharm's run/debug options, but it was a painful process and I could not come up with something better than running the above in the pycharm terminal, outside of wrapping the above in some `flash_*.sh` shell scripts for easier running.

### C Usage

Ubuntu setup:

```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential libstdc++-arm-none-eabi-newlib

# Then copied cmake (https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/external/pico_sdk_import.cmake) file to project.
# Then created a `CMakeLists.txt` file to utilize this.
```

Note: Started going down this route, stopped and gone back to Python for a bit.

### Resources

- [Raspberry Pi Python PDF](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf)
- [Python Syntax](https://learnxinyminutes.com/docs/python/)
- [MicroPython RP2 docs](https://docs.micropython.org/en/latest/rp2/quickref.html)
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