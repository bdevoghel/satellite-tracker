import argparse
import requests
import json
from time import time, sleep
from datetime import datetime

from secrets import api_key

# TODO add docstrings


def call_api(sat, lat, lon, alt, count, verbose=False):
    sec = min(count, 300)  # as set by N2YO api
    response = requests.get(f"https://api.n2yo.com/rest/v1/satellite/positions/{sat}/{lat}/{lon}/{alt}/{sec}/&apiKey={api_key}")
    data = response.json()
    if verbose > 1:
        print(f"API RESPONSE at t={int(time())} (#{data['info']['transactionscount']}) with {len(data['positions'])} positions - params : /{sat}/{lat}/{lon}/{alt}/{sec} ")
    return data


def retrieve_logfile(filename):
    with open(filename) as f:
        trace = json.loads(f.read())
        print(trace)
    return trace


def get_data(testing, **kwargs):
    if testing:
        return retrieve_logfile("testing_trace.json")  # TODO take log file as parameter
    else:
        return call_api(**kwargs)


def get_test_data(verbose=False):
    # TODO
    now = int(time())
    interval = 1
    data = {
            "info":{"satname":"TESTING","satid":-1},
            "positions":[
                {"azimuth":45.0,"elevation":-90.0,"timestamp":now+interval*1,"eclipsed":True},
                {"azimuth":135.0,"elevation":-45.0,"timestamp":now+interval*2,"eclipsed":False},
                {"azimuth":225.0,"elevation":-0.0,"timestamp":now+interval*3,"eclipsed":True},
                {"azimuth":315.0,"elevation":45.0,"timestamp":now+interval*4,"eclipsed":False},
                {"azimuth":45.0,"elevation":90.0,"timestamp":now+interval*5,"eclipsed":True},
            ]}
    duration = len(data['positions'])
    return data, duration, interval


def get_cardinal_direction(azimuth):
    if 45.0 < azimuth < 135.0:
        return 'E'
    if 135.0 <= azimuth <= 225.0:
        return 'S'
    if 225.0 < azimuth < 315.0:
        return 'W'
    
    return 'N'
    

def log_tracking(position, sat_name=None, sat_id=None, **kwargs):
    timestamp, lat, lon, alt, azimuth, elevation, eclipsed = position.get('timestamp', '???'), position.get('satlatitude', '???'), position.get('satlongitude', '???'), position.get('sataltitude', '???'), position.get('azimuth', '???'), position.get('elevation', '???'), position.get('eclipsed', '???')
    eclipsed_str = "eclipsed" if eclipsed else "in daylight"
    time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if isinstance(timestamp, int) else timestamp

    print(f"{time} - {sat_name} (id:{sat_id}) is at " +
            f"lat:{lat:{'7.2f' if isinstance(lat, float) else ''}} " +
            f"lon:{lon:{'7.2f' if isinstance(lon, float) else ''}} " +
            f"alt:{alt:>{'7.2f' if isinstance(alt, float) else ''}}. " +
            f"Look at " +
            f"{azimuth:>{'7.2f' if isinstance(azimuth, float) else ''}}°{get_cardinal_direction(azimuth) if isinstance(azimuth, float) else 'N'} and " +
            f"{elevation:{'6.2f' if isinstance(elevation, float) else ''}}° elevation. " +
            f"It is {eclipsed_str}.")


def list_of_dict_with_timestamps_to_dict(a: list) -> dict:
    d = {int(e['timestamp']):e for e in a}
    timestamps = list(d.keys())
    d['max'] = max(timestamps)
    d['min'] = min(timestamps)
    return d


def main(sat, lat, lon, alt, duration=1, interval=1, track=log_tracking, testing=False, verbose=False):
    # Get first batch of info
    if testing>1:
        data, duration, interval = get_test_data(verbose=verbose)
    else:
        data = get_data(testing=testing, sat=sat, lat=lat, lon=lon, alt=alt, count=duration+20, verbose=verbose)  # duration+20 is to account for N2YO server timestamp drift (bug on their side ?)
    info = data['info']

    # Parse future satellite positions into dict {timestamp:position}
    positions_cache = list_of_dict_with_timestamps_to_dict(data['positions'])

    try:
        while duration > 0:
            now = int(time())  # TODO correct all now computations for when testing is True : timestamp do not match anymore

            # Update cache if positions are outdated
            if positions_cache['max'] < now:
                data = get_data(testing=testing, sat=sat, lat=lat, lon=lon, alt=alt, count=duration, verbose=verbose)
                positions_cache =  list_of_dict_with_timestamps_to_dict(data['positions'])
            # Wait if first position in in the future
            if positions_cache['min'] > now:
                sleep(positions_cache['min'] - now)
                now = positions_cache['min']
            
            # Tracking callback
            track(sat_name=info['satname'], sat_id=info['satid'], position=positions_cache[now])

            duration -= interval
            if duration > 0:
                sleep(interval)
    except KeyboardInterrupt:
        print("KeyboardInterrupt", end=' - ')
    if verbose > 1:
        print("Tracking completed")


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
    parser.add_argument('-t', '--testing', action='count', default=0, help="TODO")

    args = parser.parse_args()
    args.duration = args.duration if args.duration != -1 else float('inf')

    return args


if __name__ == '__main__':

    args = parse_args()
    main(args.sat, args.lat, args.lon, args.alt, duration=args.duration, interval=args.interval, testing=args.testing, verbose=args.verbose)
