"""
HD44780 driver class for micropython.
Written using these pages as references:
https://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
https://www.glennklockwood.com/electronics/hd44780-lcd-display.html
https://www.sparkfun.com/datasheets/LCD/HD44780.pdf

Operates in 4-bit mode and therefore only needs to use data pins
4-7, plus RS + Enable.
"""
import utime


class HD44780:

    def __init__(self, rs, enable, data4, data5, data6, data7):
        """
        :type rs:machine.Pin
        :type enable:machine.Pin
        :type data4:machine.Pin
        :type data5:machine.Pin
        :type data6:machine.Pin
        :type data7:machine.Pin
        """
        self.pin_rs = rs
        self.pin_enable = enable
        self.pin_data4 = data4
        self.pin_data5 = data5
        self.pin_data6 = data6
        self.pin_data7 = data7
        self._initialize()

    def _initialize(self):
        # Init code sequence with waits as per datasheet
        utime.sleep_ms(15)
        self._send_nibble(0x3)
        utime.sleep_us(4100)
        self._send_nibble(0x3)
        utime.sleep_us(100)
        self._send_nibble(0x3)
        self._send_nibble(0x2)

        self._send_byte(0x28)  # 1[010]00 where [bits] = [0=Datalen(4 bit), 1=num_lines(2), 0=fontsize(5x8)]
        self._send_byte(0x06)  # 000110 Cursor move direction, LTR
        self._send_byte(0x0C)  # 001[100] where [bits] = [1=Display On, 0=Cursor Off, 0=Blink Off]
        self._send_clear_function()

    def _send_byte(self, byte, character_mode=False):
        # Write out nibbles seperated with pulse
        self._send_nibble(byte >> 4, character_mode)
        self._send_nibble(byte & 0xF, character_mode)

    def _pulse_enable(self):
        utime.sleep_us(1)
        self.pin_enable.value(1)
        utime.sleep_us(1)
        self.pin_enable.value(0)
        utime.sleep_us(37)

    def _send_nibble(self, nibble, character_mode=False):
        # Set to active = character_mode, inactive = command mode.
        self.pin_rs.value(character_mode)

        self.pin_data4.value(nibble & 0x01 is 0x01)
        self.pin_data5.value(nibble & 0x02 is 0x02)
        self.pin_data6.value(nibble & 0x04 is 0x04)
        self.pin_data7.value(nibble & 0x08 is 0x08)

        self._pulse_enable()

    def _send_clear_function(self):
        self._send_byte(0x01)

    def write(self, message: str, clear=True):
        if clear:
            self._send_clear_function()

        # Split input to two 16-max char lines for the display before writing them out
        lines = list(map(lambda s: s[:16], message.split("\n", 2)))
        multiline = True if len(lines) is 2 else False

        for index, line in enumerate(lines):
            # Manually set the cursor position if we're handling multi-line data
            # So that text shows on the correct lines in the right place.
            if multiline:
                self._send_byte(0x80 if index is 0 else 0xc0)

            # Send through the characters of the line
            for char in line:
                self._send_byte(ord(char), True)
