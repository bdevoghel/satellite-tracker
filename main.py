import argparse
from functools import partial

import tracker
try:
    from servo import Servo
    from stepper import Stepper
    from led import Led
    use_gpio = True
except ModuleNotFoundError:
    use_gpio = False


def pointer(position, stepper, servo, led, verbose, **kwargs):
    if verbose > 0:
        tracker.log_tracking(position, **kwargs)

    if servo is not None:
        servo.point(position['elevation'], verbose=verbose)
    if stepper is not None:
        stepper.point(position['azimuth'], verbose=verbose)
    if led is not None:
        led.flip(not position['eclipsed'], verbose=verbose)

def main(sat, lat, lon, alt, duration, interval, testing=True, verbose=False):
    try:
        # Set up motors
        # TODO generalize pins (take in as arguments)
        if use_gpio:
            stepper = Stepper(direction_pin=20, step_pin=21, enable_pin=16, verbose=verbose)
            servo = Servo(pwm_pin=23, mid_angle=0, verbose=verbose)
            led = Led(led_pin=26, verbose=verbose)
        else:
            stepper, servo, led = None, None, None

        # Test motors
        if testing and use_gpio:
            stepper.test(verbose=verbose)
            servo.test(verbose=verbose)
            led.test(verbose=verbose)
        
        # Define tracking callback and start tracking
        track_callback = partial(pointer, stepper=stepper, servo=servo, led=led, verbose=verbose)
        tracker.main(sat, lat, lon, alt, duration=duration, interval=interval, testing=testing, verbose=verbose, track=track_callback)
    finally:
        # Clean up motors
        if use_gpio:
            stepper.clean(verbose=verbose)
            servo.clean(verbose=verbose)
            led.clean(verbose=verbose)

    print(f"Pointing to sat:{sat} terminated")


if __name__ == '__main__':

    args = tracker.parse_args()
    main(args.sat, args.lat, args.lon, args.alt, args.duration, args.interval, args.testing, args.verbose)
