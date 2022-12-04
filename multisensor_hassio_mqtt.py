import json
import machine
import time
import network
import uasyncio as asyncio
from umqtt.simple import MQTTClient
import config
from libraries import ahtx0

# https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html

# LED Pins
sys_led = machine.Pin("LED", machine.Pin.OUT)
g_led = machine.Pin(0, machine.Pin.OUT)
r_led = machine.Pin(2, machine.Pin.OUT)
# Input/IO Pins
btn = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
m_sens = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_DOWN)
th_sda = machine.Pin(16) # th = temp+humidity (AHT20)
th_scl = machine.Pin(17)

# Globals
mqtt_client = None

# Busses & Wrapped Sensors
i2c0 = machine.I2C(0, sda=th_sda, scl=th_scl, freq=400000)
th_sensor = ahtx0.AHT10(i2c0)


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Disable power-save mode
    wlan.connect(config.wifi_ssid, config.wifi_pass)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])


def mqtt_connect():
    client = MQTTClient(
        config.mqtt_client_id,
        config.mqtt_server,
        keepalive=3600,
        user=config.mqtt_user,
        password=config.mqtt_pass
    )
    client.connect()
    print('Connected to %s MQTT Broker' % (config.mqtt_server))
    return client


def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()


def update_sensor_mqtt_state(sensor):
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    mqtt_client.publish(state_topic.encode(), sensor.status.encode())


def update_sensor_mqtt_config(sensor):
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    config_topic = 'homeassistant/{type}/{id}/config'.format(type=sensor.type, id=sensor.id)
    configure_payload = {
        "name": sensor.name,
        "state_topic": state_topic,
        "unique_id": sensor.id
    }
    
    if sensor.device_class:
        configure_payload["device_class"] = sensor.device_class
        
    if sensor.unit_of_measurement:
        configure_payload["unit_of_measurement"] = sensor.unit_of_measurement

    mqtt_client.publish(config_topic.encode(), json.dumps(configure_payload).encode())


async def update_sensor(sensor):
    while True:
        changed = sensor.check_status()
        # print("Check sensor status, sensor: {sensor}, status: {status}, changed: {changed}".format(sensor=sensor.id,status=str(sensor.status), changed=str(changed)))
        if changed:
            update_sensor_mqtt_state(sensor)
        await asyncio.sleep_ms(sensor.poll_rate_ms)


async def start_polling_sensors(sensors):
    for index, sensor in enumerate(sensors):
        print("Creating poll for {} every {}ms".format(sensor.name, sensor.poll_rate_ms))
        asyncio.create_task(update_sensor(sensor))
    while True:
        await asyncio.sleep_ms(15000)
                

class Sensor:

    def __init__(self, name, id, type, status_getter, device_class='', unit_of_measurement='', poll_rate_ms=1000):
        self.name = name
        self.id = id
        self.type = type # https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
        self.status_getter = status_getter
        self.device_class = device_class # https://www.home-assistant.io/integrations/sensor/#device-class
        self.poll_rate_ms = poll_rate_ms
        self.status = None
        self.on_change_handlers = []
        self.unit_of_measurement = unit_of_measurement

    def check_status(self):
        status = self.status_getter()
        changed = status != self.status
        if changed:
            self.status = status
            for handler in self.on_change_handlers:
                handler(status, self)
        return changed

    def add_on_change_handler(self, handler):
        self.on_change_handlers.append(handler)


# Sensor Configuration

proximity_sensor = Sensor(
    name='Picow A Proximity',
    id='picow_a_proximity',
    type='binary_sensor',
    status_getter=(lambda: 'ON' if m_sens.value() else 'OFF'),
    device_class='motion',
    poll_rate_ms=2
)

button_sensor = Sensor(
    name='Picow A Button',
    id='picow_a_button',
    type='binary_sensor',
    status_getter=(lambda: 'ON' if btn.value() else 'OFF'),
    poll_rate_ms=2
)

temp_sensor = Sensor(
    name='Picow A Temperature',
    id='picow_a_temp',
    type='sensor',
    status_getter=(lambda: ("%.2f" % th_sensor.temperature)),
    device_class='temperature',
    poll_rate_ms=60000,
    unit_of_measurement='°C'
)

humidity_sensor = Sensor(
    name='Picow A Relative Humidity',
    id='picow_a_rh',
    type='sensor',
    status_getter=(lambda: ("%.2f" % th_sensor.relative_humidity)),
    device_class='humidity',
    poll_rate_ms=60000,
    unit_of_measurement='%'
)

# List to hold all our sensors
sensors = [proximity_sensor, button_sensor, temp_sensor, humidity_sensor]

# Show the proximity sensor state via green LED
proximity_sensor.add_on_change_handler((lambda val, sensor: g_led.value(val == 'ON')))
# Show the button sensor state via green LED
button_sensor.add_on_change_handler((lambda val, sensor: r_led.value(val == 'ON')))
button_sensor.add_on_change_handler((lambda val, sensor: print("Button changed to " + val)))

try:
    wifi_connect()
    mqtt_client = mqtt_connect()
    for sensor in sensors:
        print(sensor.id)
        update_sensor_mqtt_config(sensor)
    asyncio.run(start_polling_sensors(sensors))
except OSError as e:
    reconnect()
finally:
    asyncio.new_event_loop()
