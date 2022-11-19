from machine import Pin
import time
import _thread

# https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/6
# http://docs.micropython.org/en/latest/rp2/quickref.html

sys_led = Pin("LED", Pin.OUT)
g_led = Pin(0, Pin.OUT)
btn = Pin(1, Pin.IN, Pin.PULL_DOWN)

light_queue = []
delay = 4
delay_ns = delay * 1000000000
btn_state = 0


def flash_led(led_pin: Pin, times: int, length: float):
    for _ in range(times):
        led_pin.on()
        time.sleep(length / 2)
        led_pin.off()
        time.sleep(length / 2)


def light_thread():
    global light_queue
    while True:
        now = time.time_ns()
        if len(light_queue) > 0:
            status_time = light_queue[0]
            status = status_time[0]
            light_time = status_time[1]
            if light_time + delay_ns <= now:
                g_led.value(status)
                del light_queue[0]
                print("update! " + str(status))


_thread.start_new_thread(light_thread, ())
while True:
    btn_val = btn.value()
    if btn_val != btn_state:
        light_queue.append((btn_val, time.time_ns()))
        btn_state = btn_val
        sys_led.value(btn_val)
        print("change! " + str(btn_val))
