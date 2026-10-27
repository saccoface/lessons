# Physical AI Lab: Cardboard Robot. Pico servo driver (MicroPython).
#
# The browser sends one command per line over USB serial:
#   "35"  or "M35"  move the mouth servo to 35 degrees   (week 1)
#   "N120"          move the neck servo to 120 degrees   (week 2)
#   "?"             answers "ROBOT READY", so the page knows it found the right board
#
# Wiring (MG90S servos, Pico held with the USB port at the top):
#   mouth signal (orange/yellow) -> GP15  (pin 20, bottom left)
#   neck signal  (orange/yellow) -> GP14  (pin 19, just above it)
#   red (power) and brown (ground) of every servo go to a breadboard's + and - rails,
#   fed 5 V by a USB charger or power bank. One jumper joins the - rail to GND (pin 23).
#   Nothing goes on VBUS (pin 40): a servo powered from the Pico resets it when it moves fast.
#
# Works on the Pico, Pico H, Pico 2 and Pico 2 W.
#
# Flash it with Thonny (thonny.org):
#   1. Hold BOOTSEL while plugging the Pico in. A drive appears: RPI-RP2 (Pico) or RP2350 (Pico 2).
#   2. Bottom-right corner > Install MicroPython. Family RP2; pick the variant that matches the
#      board (for example "Raspberry Pi - Pico 2 W"). Install, then close the window.
#   3. Unplug and replug without BOOTSEL. Bottom-right corner > MicroPython (Raspberry Pi Pico),
#      and wait for >>> in the Shell. Press Stop if you don't see it.
#   4. Paste this file into the editor at the top (not the Shell), then
#      File > Save as > Raspberry Pi Pico > main.py. It runs on every power-up.
#      If Save as never asks where to save, Thonny isn't connected to the board: redo step 3.
#   5. Quit Thonny before opening the lesson page. Only one program can use the Pico at a time.
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
