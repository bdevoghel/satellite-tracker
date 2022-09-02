import lgpio
from time import sleep

# TODO add docstrings


class Servo:
    def __init__(self, pwm_pin, mid_angle=90, verbose=False):
        if verbose > 1:
            print(f"SETTING UP {__class__.__name__}")

        self.DUTY_MIN = 3.2  # minimum duty cycle ratio
        self.DUTY_MAX = 12.1  # maximum duty cycle ratio
        self.JITTER_DELAY = 0.2  # minimum delay to prevent servo from jittering
        self.FREQ = 50  # 50Hz pulse

        # Determine angle range
        mid_angle_possibilities = [0, 90] # 0 => angle:[-90, 90] ; 90 => angle:[0, 180]
        assert mid_angle in mid_angle_possibilities, f"mid_angle must be one of {mid_angle_possibilities}"
        self.min_angle = -90 + mid_angle
        self.mid_angle = mid_angle
        self.max_angle = 90 + mid_angle

        self.pwm_pin = pwm_pin

        # Open gpio chip and set pin as pulse width modulation (PWM) output
        self.gpio_handle = lgpio.gpiochip_open(0)
        lgpio.tx_pwm(self.gpio_handle, pwm_pin, self.FREQ, 0)  # start PWM with pulse off

    def test(self, verbose=True):
        # Go to mid, max, min angles
        if verbose > 1:
            print(f"TESTING {__class__.__name__}")
        
        self.point(self.mid_angle, verbose=verbose, jitter_delay_factor=2)
        sleep(.2)
        self.point(self.mid_angle)
        sleep(.5)
        self.point((self.mid_angle+self.max_angle)/2, verbose=verbose)
        sleep(.5)
        self.point(self.max_angle, verbose=verbose)
        sleep(.5)
        self.point((self.mid_angle+self.max_angle)/2, verbose=verbose)
        sleep(.5)
        self.point(self.mid_angle, verbose=verbose)
        sleep(.5)
        self.point((self.mid_angle+self.min_angle)/2, verbose=verbose)
        sleep(.5)
        self.point(self.min_angle, verbose=verbose)
        sleep(.5)
        self.point(self.mid_angle, verbose=verbose, jitter_delay_factor=2)
        sleep(.2)
    
    def point(self, angle, verbose=False, jitter_delay_factor=1):
        # Correct angle wrt mid_angle
        angle = angle + (90 - self.mid_angle)
        
        if verbose > 2:
            print(f"   - {__class__.__name__} pointing to {angle - 90 + self.mid_angle:.2f}°")

        # Change duty cycle
        duty = min(self.DUTY_MAX, self.DUTY_MIN + angle / (180. / (self.DUTY_MAX-self.DUTY_MIN)))
        lgpio.tx_pwm(self.gpio_handle, self.pwm_pin, self.FREQ, duty)

        # Turn off to avoid jittering
        sleep(self.JITTER_DELAY * jitter_delay_factor)
        lgpio.tx_pwm(self.gpio_handle, self.pwm_pin, self.FREQ, 0)

    def clean(self, verbose=False):
        if verbose > 1:
            print(f"CLEANING {__class__.__name__}")
        
        lgpio.gpiochip_close(self.gpio_handle)
