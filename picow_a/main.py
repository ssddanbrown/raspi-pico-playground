import json
import machine
import time
import network
from umqtt.simple import MQTTClient
import config
from libraries import ahtx0

# https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html

device_name = 'Picow A'
device_id = device_name.lower().replace(' ', '_')

# LED Pins
sys_led = machine.Pin("LED", machine.Pin.OUT)
g_led = machine.Pin(22, machine.Pin.OUT)
r_led = machine.Pin(28, machine.Pin.OUT)
g_led.off()
r_led.off()
sys_led.off()

# Input/IO Pins
btn = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
m_sens = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN)

th_pow = machine.Pin(10, machine.Pin.OUT, None, value=1)
th_sda = machine.Pin(20)  # th = temp+humidity (AHT20)
th_scl = machine.Pin(21)

# Globals
mqtt_client = None
wlan = None

# Busses & Wrapped Sensors
i2c0 = machine.I2C(0, sda=th_sda, scl=th_scl, freq=100000)
th_sensor = ahtx0.AHT10(i2c0)


# Wifi & MQTT

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # wlan.config(pm=0xa11140)  # Disable power-save mode
    wlan.connect(config.wifi_ssid, config.wifi_pass)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(3)

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')

    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    return wlan


def mqtt_connect():
    client = MQTTClient(
        device_id,
        config.mqtt_server,
        keepalive=3600,
        user=config.mqtt_user,
        password=config.mqtt_pass
    )
    client.connect(True)
    print('Connected to %s MQTT Broker' % (config.mqtt_server))
    r_led.on()
    return client


def reconnect():
    global wlan
    global mqtt_client
    r_led.off()
    print('Failed to connect to the MQTT Broker. Waiting 15 seconds then reconnecting...')
    wlan = wifi_connect()
    mqtt_client = mqtt_connect()

def reset():
    r_led.on()
    time.sleep(2)
    r_led.off()
    time.sleep(2)
    print('Failed with error. Waiting 15 seconds then resetting')
    time.sleep(11)
    r_led.on()
    time.sleep(.5)
    r_led.off()
    machine.reset()
    

# Button and light handling

lights_enabled = True
button_down_at = None
button_state = 0


def button_handler(pin):
    global button_down_at
    global lights_enabled
    global button_state
    
    if btn.value() == button_state:
        return
    button_state = btn.value()
    
    if button_state:
            global button_down_at
            button_down_at = time.ticks_ms()   
    else:    
        press_time = time.ticks_diff(time.ticks_ms(), button_down_at)

        if press_time > 3000:
            print("Resetting device due to long button press")
            for i in range(2):
                r_led.on()
                time.sleep(1)
                r_led.off()
                time.sleep(1)
            machine.reset()
        elif press_time > 200:
            # Toggle lights on short press
            lights_enabled = not lights_enabled
            print("Toggling lights {} from button press".format("on" if lights_enabled else "off"))
            r_led.value(lights_enabled)
            g_led.off()
            sys_led.off()


btn.irq(handler=button_handler, trigger=machine.Pin.IRQ_RISING|machine.Pin.IRQ_FALLING)

# Sensor logic


def update_sensor_mqtt_state(sensor):
    if wlan.isconnected() is False:
        return reconnect()
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    mqtt_client.publish(state_topic.encode(), sensor.status.encode())


def update_sensor_mqtt_config(sensor):
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    config_topic = 'homeassistant/{type}/{id}/config'.format(type=sensor.type, id=sensor.id)
    configure_payload = {
        "name": sensor.name,
        "state_topic": state_topic,
        "unique_id": sensor.id,
        "device": {
            "name": device_name,
            "identifiers": [device_id]
        }
    }

    if sensor.device_class:
        configure_payload["device_class"] = sensor.device_class

    if sensor.unit_of_measurement:
        configure_payload["unit_of_measurement"] = sensor.unit_of_measurement

    mqtt_client.publish(config_topic.encode(), json.dumps(configure_payload).encode())


def update_sensor(sensor):
    changed = sensor.check_status()
    #print("Check sensor status, sensor: {sensor}, status: {status}, changed: {changed}".format(sensor=sensor.id,status=str(sensor.status), changed=str(changed)))
    if changed:
        update_sensor_mqtt_state(sensor)


class Sensor:

    def __init__(self, name, id, type, status_getter, device_class='', unit_of_measurement='', poll_rate_ms=1000):
        self.name = name
        self.id = id
        self.type = type  # https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
        self.status_getter = status_getter
        self.device_class = device_class  # https://www.home-assistant.io/integrations/sensor/#device-class
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
    name=device_name + ' Proximity',
    id=device_id + '_proximity',
    type='binary_sensor',
    status_getter=(lambda: 'ON' if m_sens.value() else 'OFF'),
    device_class='motion',
    poll_rate_ms=500
)

temp_sensor = Sensor(
    name=device_name + ' Temperature',
    id=device_id + '_temp',
    type='sensor',
    status_getter=(lambda: ("%.2f" % (th_sensor.temperature - 5))), # Rough adjustment of reading to account for drift over time
    device_class='temperature',
    poll_rate_ms=60000,
    unit_of_measurement='°C'
)

humidity_sensor = Sensor(
    name=device_name + ' Relative Humidity',
    id=device_id + '_rh',
    type='sensor',
    status_getter=(lambda: ("%.2f" % th_sensor.relative_humidity)),
    device_class='humidity',
    poll_rate_ms=60000,
    unit_of_measurement='%'
)

# List to hold all our sensors
sensors = [proximity_sensor, temp_sensor, humidity_sensor]

# Show the proximity sensor state via green LED
proximity_sensor.add_on_change_handler((lambda val, sensor: g_led.value(lights_enabled and val == 'ON')))
proximity_sensor.add_on_change_handler((lambda val, sensor: print("Proximity:" + val)))

try:
    wlan = wifi_connect()
    mqtt_client = mqtt_connect()
    sensor_check_times = []
    last_sys_led_change = time.ticks_ms()

    # Update sensor config
    for sensor in sensors:
        update_sensor_mqtt_config(sensor)
        update_sensor(sensor)
        sensor_check_times.append(time.ticks_ms())

    # Poll sensors
    while True:
        time.sleep(1)
        now = time.ticks_ms()
        sensor_next_polls = []

        # Toggle sys led to indicate activity, limited to half-second changes at minimum
        # so flashing is visible.
        if lights_enabled and time.ticks_diff(now, last_sys_led_change) > 200:
            sys_led.value(not sys_led.value())
            last_sys_led_change = time.ticks_ms()
            
        # We update each sensor, if it's time, and store the expected time
        # until we next need to poll the sensor.
        for index, sensor in enumerate(sensors):
            last_check = sensor_check_times[index]
            check_delta = time.ticks_diff(now, last_check)
            time_to_poll =  sensor.poll_rate_ms - check_delta
            #print("check for {}, delta: {}, poll_rate: {}, ttp: {}".format(sensor.id, check_delta, sensor.poll_rate_ms, time_to_poll))
            if time_to_poll <= 0:
                update_sensor(sensor)
                time_to_poll = sensor.poll_rate_ms
                sensor_check_times[index] = now
            sensor_next_polls.append(time_to_poll)


        # We look to the minimum next poll and attempt to sleep until then
        next_poll = min(sensor_next_polls)
        if next_poll > 0:
            time.sleep_ms(next_poll)

except:
    reset()
