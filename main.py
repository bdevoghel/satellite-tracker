import argparse
from functools import partial
import logging

from rich.logging import RichHandler

from pointing import pointer

logging.basicConfig(
    level="DEBUG",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
try:
    from tracking import Servo,Stepper,Led
    use_gpio = True
    logger.info("GPIO libraries imported")
except ModuleNotFoundError:
    use_gpio = False


def tracker(position, stepper, servo, led, verbose, **kwargs):
    if verbose > 0:
        pointer.log_tracking(position, **kwargs)

    if servo is not None:
        servo.point(position['elevation'], verbose=verbose)
    if stepper is not None:
        stepper.point(position['azimuth'], verbose=verbose)
    if led is not None:
        led.flip(not position['eclipsed'], verbose=verbose)

def track_satellite(sat, lat, lon, alt, duration, interval, testing=True, verbose=False):
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
        track_callback = partial(tracker, stepper=stepper, servo=servo, led=led, verbose=verbose)
        pointer.start_pointing(sat, lat, lon, alt, duration=duration, interval=interval, testing=testing, verbose=verbose, track=track_callback)
    finally:
        # Clean up motors
        if use_gpio:
            stepper.clean(verbose=verbose)
            servo.clean(verbose=verbose)
            led.clean(verbose=verbose)

    logger.info(f"Pointing to sat:{sat} terminated")


def parse_args():
    parser = argparse.ArgumentParser(description="Track a satellite's position with respect to an observer location.")
    parser.add_argument('-s', '--sat', action='store', default=25544, type=int, help="NORAD id of satellite to track") # 25544 corresponds to ISS
    parser.add_argument('-l', '--lat', action='store', default=.0, type=float, help="Observer's latitide (decimal degrees format)")
    parser.add_argument('-L', '--lon', action='store', default=.0, type=float, help="Observer's longitude (decimal degrees format)")
    parser.add_argument('-a', '--alt', action='store', default=.0, type=float, help="Observer's altitude above sea level in meters")
    parser.add_argument('-d', '--duration', action='store', default=1, type=int, help="Duration of the tracking in seconds. -1 for indefinite")
    parser.add_argument('-i', '--interval', action='store', default=1., type=float, help="Interval between two track callbacks. Accurate to the second")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Increase output verbosity")

    # TODO bypass api for testing pointer -- TODO adapt timestamp utilization (see now computation)
    parser.add_argument('-t', '--testing', action='store_true', help="TODO")

    args = parser.parse_args()
    args.duration = args.duration if args.duration != -1 else float('inf')

    return args


def main():
    args = parse_args()
    logger.debug(args)
    track_satellite(args.sat, args.lat, args.lon, args.alt, args.duration, args.interval, args.testing, args.verbose)


if __name__ == '__main__':
    main()