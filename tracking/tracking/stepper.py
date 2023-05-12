import logging
from time import sleep

import lgpio

logger = logging.getLogger(__name__)


class Stepper:
    def __init__(self, direction_pin, step_pin, enable_pin, verbose=False):
        if verbose > 1:
            logger.info(f"SETTING UP {__class__.__name__}")

        self.MIN_DELAY = 0.005  # minimum delay between steps
        self.CW = 0  # clockwise value
        self.ENABLED = False  # depends if pin in enable_high or _low
        self.SPR = (
            400  # steps per revolution (360/step_angle) TODO implement microstepping ?
        )

        # Assume initial pointing is true North
        self.current_step = 0
        self.direction = 1

        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin

        # Open gpio chip and set pins as output
        self.gpio_handle = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self.gpio_handle, direction_pin)
        lgpio.gpio_claim_output(self.gpio_handle, step_pin)
        lgpio.gpio_claim_output(self.gpio_handle, enable_pin)

        lgpio.gpio_write(self.gpio_handle, self.direction_pin, self.CW)
        lgpio.gpio_write(self.gpio_handle, self.enable_pin, self.ENABLED)

    def test(self, verbose=False):
        # Do full tour, back and forth
        if verbose > 1:
            logger.info(f"TESTING {__class__.__name__}")

        self.point(90)
        self.point(180, verbose=verbose)
        self.point(270)
        self.point(0, verbose=verbose)
        sleep(0.5)
        self.point(270)
        self.point(180, verbose=verbose)
        self.point(90)
        self.point(0, verbose=verbose)

    def point(self, angle, verbose=False):
        if verbose > 2:
            logger.info(f"   - {__class__.__name__} pointing to {angle:.2f}°")

        # Determine orientation to take
        step_target = int((angle / 360.0 * self.SPR) % self.SPR)
        self.change_direction(
            (((step_target + self.SPR - self.current_step) % self.SPR) < self.SPR / 2)
            == self.CW
        )

        while step_target != self.current_step:
            self.step()

    def step(self, delay=0):
        delay = max(delay, self.MIN_DELAY)

        # Pulse for 1 step
        lgpio.gpio_write(self.gpio_handle, self.step_pin, True)
        sleep(delay)
        lgpio.gpio_write(self.gpio_handle, self.step_pin, False)
        sleep(delay)

        self.current_step = (self.current_step + self.direction + self.SPR) % self.SPR

    def change_direction(self, direction):
        lgpio.gpio_write(self.gpio_handle, self.direction_pin, direction)
        self.direction = 1 if direction == self.CW else -1

    def clean(self, verbose=False):
        if verbose > 1:
            logger.info(f"CLEANING {__class__.__name__}")

        self.point(0)
        lgpio.gpio_write(self.gpio_handle, self.enable_pin, not self.ENABLED)
        lgpio.gpiochip_close(self.gpio_handle)
