"""Module to compute the pointing angle to a satellite from a given location."""
import json
import logging
import os
from datetime import datetime
from time import sleep, time

import requests

N2YO_API_KEY = os.environ.get("N2YO_API_KEY", None)

logger = logging.getLogger(__name__)

# TODO add docstrings


def call_api(sat, lat, lon, alt, count, verbose=False):
    """Call N2YO API to get satellite positions."""
    sec = min(count, 300)  # as set by N2YO api
    response = requests.get(
        f"https://api.n2yo.com/rest/v1/satellite/positions/{sat}/{lat}/{lon}/{alt}/{sec}/&apiKey={N2YO_API_KEY}"
    )
    response.raise_for_status()
    data = response.json()
    if data.get("error", False):
        raise ValueError(f"API ERROR: {data['error']}")
    logger.debug(
        f"API RESPONSE at t={int(time())} (#{data['info']['transactionscount']}) with {len(data['positions'])} positions - params : /{sat}/{lat}/{lon}/{alt}/{sec} "
    )
    return data


def retrieve_logfile(filename):
    """Retrieve data from a log file."""
    with open(filename) as f:
        trace = json.loads(f.read())
    return trace


def get_data(testing, **kwargs):
    if testing:
        data = retrieve_logfile("testing_trace.json")  # TODO take log file as parameter
    else:
        data = call_api(**kwargs)
    logger.debug(f"{data=}")
    return data


def get_test_data(verbose=False):
    # TODO
    now = int(time())
    interval = 1
    data = {
        "info": {"satname": "TESTING", "satid": -1},
        "positions": [
            {
                "azimuth": 45.0,
                "elevation": -90.0,
                "timestamp": now + interval * 1,
                "eclipsed": True,
            },
            {
                "azimuth": 135.0,
                "elevation": -45.0,
                "timestamp": now + interval * 2,
                "eclipsed": False,
            },
            {
                "azimuth": 225.0,
                "elevation": -0.0,
                "timestamp": now + interval * 3,
                "eclipsed": True,
            },
            {
                "azimuth": 315.0,
                "elevation": 45.0,
                "timestamp": now + interval * 4,
                "eclipsed": False,
            },
            {
                "azimuth": 45.0,
                "elevation": 90.0,
                "timestamp": now + interval * 5,
                "eclipsed": True,
            },
        ],
    }
    duration = len(data["positions"])
    return data, duration, interval


def get_cardinal_direction(azimuth):
    if 45.0 < azimuth < 135.0:
        return "E"
    if 135.0 <= azimuth <= 225.0:
        return "S"
    if 225.0 < azimuth < 315.0:
        return "W"

    return "N"


def log_tracking(position, sat_name=None, sat_id=None, **kwargs):
    timestamp, lat, lon, alt, azimuth, elevation, eclipsed = (
        position.get("timestamp", "???"),
        position.get("satlatitude", "???"),
        position.get("satlongitude", "???"),
        position.get("sataltitude", "???"),
        position.get("azimuth", "???"),
        position.get("elevation", "???"),
        position.get("eclipsed", "???"),
    )
    eclipsed_str = "eclipsed" if eclipsed else "in daylight"
    time = (
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(timestamp, int)
        else timestamp
    )

    logger.info(
        f"{time} - {sat_name} (id:{sat_id}) is at "
        + f"lat:{lat:{'7.2f' if isinstance(lat, float) else ''}} "
        + f"lon:{lon:{'7.2f' if isinstance(lon, float) else ''}} "
        + f"alt:{alt:>{'7.2f' if isinstance(alt, float) else ''}}. "
        + "Look at "
        + f"{azimuth:>{'7.2f' if isinstance(azimuth, float) else ''}}°{get_cardinal_direction(azimuth) if isinstance(azimuth, float) else 'N'} and "
        + f"{elevation:{'6.2f' if isinstance(elevation, float) else ''}}° elevation. "
        + f"It is {eclipsed_str}."
    )


def list_of_dict_with_timestamps_to_dict(a: list) -> dict:
    d = {int(e["timestamp"]): e for e in a}
    timestamps = list(d.keys())
    d["max"] = max(timestamps)
    d["min"] = min(timestamps)
    return d


def start_pointing(
    sat,
    lat,
    lon,
    alt,
    duration=1,
    interval=1,
    track=log_tracking,
    testing=False,
    verbose=False,
):
    # Get first batch of info
    if testing > 1:
        data, duration, interval = get_test_data(verbose=verbose)
    else:
        data = get_data(
            testing=testing,
            sat=sat,
            lat=lat,
            lon=lon,
            alt=alt,
            count=duration + 20,
            verbose=verbose,
        )  # duration+20 is to account for N2YO server timestamp drift (bug on their side ?)
    info = data["info"]

    # Parse future satellite positions into dict {timestamp:position}
    positions_cache = list_of_dict_with_timestamps_to_dict(data["positions"])

    try:
        while duration > 0:
            now = positions_cache["min"] if testing else int(time())

            # Update cache if positions are outdated
            if positions_cache["max"] < now:
                data = get_data(
                    testing=testing,
                    sat=sat,
                    lat=lat,
                    lon=lon,
                    alt=alt,
                    count=duration,
                    verbose=verbose,
                )
                positions_cache = list_of_dict_with_timestamps_to_dict(
                    data["positions"]
                )
            # Wait if first position in in the future
            if positions_cache["min"] > now:
                sleep(positions_cache["min"] - now)
                now = positions_cache["min"]

            # Tracking callback
            track(
                sat_name=info["satname"],
                sat_id=info["satid"],
                position=positions_cache[now],
            )

            duration -= interval
            if duration > 0:
                sleep(interval)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt")
    finally:
        if verbose > 1:
            logger.info("Tracking completed")
