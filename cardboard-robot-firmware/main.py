# Physical AI Lab: Robot desk assistant. Pico servo driver (MicroPython), mouth and eyes.
#
# The browser sends one command per line over USB serial:
#   "35"  or "M35"  move the mouth servo to 35 degrees   (Class 1)
#   "N120"          move the neck servo to 120 degrees   (optional neck)
#   "L" / "R"       both eyes look left / right for about 2 s, then back to centre   (Class 2 eyes)
#   "E"             eyes back to centre now
#   "X"             cross the eyes for about 2 s, then back to centre
#   "?"             answers "ROBOT READY", so the page knows it found the right board
#
# While the mouth is moving (the robot is talking), the eyes glance a little every 3-6 s
# on their own. When it's quiet, the eye servos switch off so they don't buzz or use power.
#
# Wiring (MG90S servos, Pico held with the USB port at the top):
#   mouth signal (orange/yellow) -> GP15  (pin 20, bottom left)
#   neck signal  (orange/yellow) -> GP14  (pin 19, just above it)
#   left eye     (orange/yellow) -> GP13  (pin 17)    right eye -> GP12 (pin 16)   (Class 2 upgrade)
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
import random
from machine import Pin, PWM

MIN_US, MAX_US = 500, 2400   # MG90S pulse range for 0 and 180 degrees
REST_MS = 1500               # stop driving a still servo after this long, so it doesn't buzz

EYE_CENTRE = 90
CROSS_LEFT, CROSS_RIGHT = 45, 135   # left eye, right eye when crossed (inward, checked on Dana's robot)
LOOK = 40                    # how far a commanded look left/right turns the eyes
GLANCE = 25                  # how far a glance while talking turns the eyes
HOLD_MS = 2000               # how long X / L / R hold before the eyes come back
TALKING_MS = 800             # mouth moved this recently = the robot is talking


class Servo:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)
        self.last = time.ticks_ms()
        self.resting = False
        self.angle = None

    def move(self, angle):
        angle = max(0, min(180, angle))
        us = MIN_US + (MAX_US - MIN_US) * angle / 180
        self.pwm.duty_u16(int(us * 65535 / 20000))
        self.last = time.ticks_ms()
        self.resting = False
        self.angle = angle

    def rest_if_idle(self):
        if not self.resting and time.ticks_diff(time.ticks_ms(), self.last) > REST_MS:
            self.pwm.duty_u16(0)
            self.resting = True


mouth = Servo(15)
neck = Servo(14)
left_eye = Servo(13)
right_eye = Servo(12)
mouth.move(90)               # the neck stays limp until the page asks for it


def eyes(left, right):
    left_eye.move(left)
    right_eye.move(right)


eyes(EYE_CENTRE, EYE_CENTRE)

mouth_moved = time.ticks_add(time.ticks_ms(), -10000)   # when the mouth last really moved
hold_until = None            # a command (X/L/R) or a glance is holding the eyes until this time
next_glance = time.ticks_ms()


def now():
    return time.ticks_ms()


def hold(ms):
    global hold_until
    hold_until = time.ticks_add(now(), ms)


def handle(cmd):
    global mouth_moved, hold_until
    if cmd == '?':
        print('ROBOT READY')
        return
    c = cmd[0]
    if c == 'X':
        eyes(CROSS_LEFT, CROSS_RIGHT)
        hold(HOLD_MS)
    elif c == 'L':
        eyes(EYE_CENTRE - LOOK, EYE_CENTRE - LOOK)
        hold(HOLD_MS)
    elif c == 'R':
        eyes(EYE_CENTRE + LOOK, EYE_CENTRE + LOOK)
        hold(HOLD_MS)
    elif c == 'E':
        eyes(EYE_CENTRE, EYE_CENTRE)
        hold_until = None
    elif c == 'N':
        try:
            neck.move(int(cmd[1:]))
        except ValueError:
            pass
    else:
        try:
            a = int(cmd.lstrip('M'))
        except ValueError:
            return
        if mouth.angle is None or abs(a - mouth.angle) >= 3:
            mouth_moved = now()
        mouth.move(a)


def update_eyes():
    global hold_until, next_glance
    t = now()
    if hold_until is not None:
        if time.ticks_diff(t, hold_until) >= 0:
            eyes(EYE_CENTRE, EYE_CENTRE)
            hold_until = None
            next_glance = time.ticks_add(t, random.randint(3000, 6000))
        return
    talking = time.ticks_diff(t, mouth_moved) < TALKING_MS
    if talking and time.ticks_diff(t, next_glance) >= 0:
        d = GLANCE if random.getrandbits(1) else -GLANCE
        eyes(EYE_CENTRE + d, EYE_CENTRE + d)
        hold(random.randint(700, 1300))
    elif not talking and time.ticks_diff(t, next_glance) >= 0:
        next_glance = time.ticks_add(t, random.randint(1000, 3000))  # first glance soon after talking starts


poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
buf = ''
print('ROBOT READY')

while True:
    if poll.poll(50):
        ch = sys.stdin.read(1)
        if ch in '\r\n':
            if buf:
                handle(buf)
            buf = ''
        elif len(buf) < 8:
            buf += ch
    update_eyes()
    mouth.rest_if_idle()
    neck.rest_if_idle()
    left_eye.rest_if_idle()
    right_eye.rest_if_idle()
