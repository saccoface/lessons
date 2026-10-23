# Physical AI Lab: Cardboard Robot. Pico servo driver (MicroPython).
#
# The browser sends one command per line over USB serial:
#   "35"  or "M35"  move the mouth servo to 35 degrees   (week 1)
#   "N120"          move the neck servo to 120 degrees   (week 4)
#   "?"             answers "ROBOT READY", so the page knows it found the right board
#
# Wiring (MG90S servos, Pico held with the USB port at the top):
#   mouth signal (orange/yellow) -> GP15  (pin 20, bottom left)
#   neck signal  (orange/yellow) -> GP14  (pin 19, just above it)
#   red (power, 5 V)             -> VBUS  (pin 40, top right)   mouth only; in week 4 both
#                                   servos move to the battery-fed breadboard instead
#   brown (ground)               -> GND   (pin 38)
#
# Flash: install MicroPython on the Pico, then save this file to the board as
# main.py (Thonny: File > Save as > Raspberry Pi Pico). It runs on every power-up.
import sys
import select
import time
from machine import Pin, PWM

MIN_US, MAX_US = 500, 2400   # MG90S pulse range for 0 and 180 degrees
REST_MS = 1500               # stop driving a still servo after this long, so it doesn't buzz


class Servo:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)
        self.last = time.ticks_ms()
        self.resting = False

    def move(self, angle):
        angle = max(0, min(180, angle))
        us = MIN_US + (MAX_US - MIN_US) * angle / 180
        self.pwm.duty_u16(int(us * 65535 / 20000))
        self.last = time.ticks_ms()
        self.resting = False

    def rest_if_idle(self):
        if not self.resting and time.ticks_diff(time.ticks_ms(), self.last) > REST_MS:
            self.pwm.duty_u16(0)
            self.resting = True


mouth = Servo(15)
neck = Servo(14)
mouth.move(90)               # the neck stays limp until the page asks for it

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
buf = ''
print('ROBOT READY')


def handle(cmd):
    if cmd == '?':
        print('ROBOT READY')
        return
    target = neck if cmd[0] == 'N' else mouth
    try:
        target.move(int(cmd.lstrip('MN')))
    except ValueError:
        pass


while True:
    if poll.poll(50):
        ch = sys.stdin.read(1)
        if ch in '\r\n':
            if buf:
                handle(buf)
            buf = ''
        elif len(buf) < 8:
            buf += ch
    else:
        mouth.rest_if_idle()
        neck.rest_if_idle()
