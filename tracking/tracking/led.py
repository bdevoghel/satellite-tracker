import logging
from time import sleep

import lgpio

logger = logging.getLogger(__name__)


class Led:
    def __init__(self, led_pin, verbose=False):
        logger.info(f"SETTING UP {__class__.__name__}")

        # Open gpio chip and set pin as output
        self.gpio_handle = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self.gpio_handle, led_pin)
        self.pin = led_pin

        # Start as off
        self.is_on = False
        self.flip(self.is_on)

    def test(self, verbose=True):
        # Blink 5 times
        logger.info(f"TESTING {__class__.__name__}")

        for _ in range(5):
            self.flip(verbose=verbose)
            sleep(0.1)
            self.flip(verbose=verbose)
            sleep(0.2)

    def flip(self, turn_on=None, verbose=False):
        # Determine if has to turn on or off
        self.is_on = turn_on if turn_on is not None else not self.is_on

        logger.info(f"   - {__class__.__name__} flip {self.is_on}")

        lgpio.gpio_write(self.gpio_handle, self.pin, self.is_on)

    def clean(self, verbose=False):
        logger.info(f"CLEANING {__class__.__name__}")

        self.flip(False)
        lgpio.gpiochip_close(self.gpio_handle)
