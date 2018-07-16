#-------------------------------------------------------------------------------
#
#  Various time handling utilities
#
# Authors:  Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

import re
from datetime import date, datetime, timedelta, tzinfo
from time import time
import math

RE_ISO_8601_DATETIME_LONG = re.compile(
    r"^(\d{4,4})-(\d{2,2})-(\d{2,2})(?:"
    r"T(\d{2,2}):(\d{2,2})"
    r"(?::(\d{2,2})(?:[.,](\d{0,6})\d*)?)?"
    r"(Z|([+-]\d{2,2})(?::(\d{2,2}))?)?"
    r")?$"
)

RE_ISO_8601_DATETIME_SHORT = re.compile(
    r"^(\d{4,4})(\d{2,2})(\d{2,2})(?:"
    r"T(\d{2,2})(\d{2,2})"
    r"(?:(\d{2,2})(?:[.,](\d{0,6})\d*)?)?"
    r"(Z|([+-]\d{2,2})(\d{2,2})?)?"
    r")?$"
)

RE_ISO_8601_DURATION = re.compile(
    r"^(?P<sign>[+-])?P"
    r"(?:(?P<years>\d+(\.\d+)?)Y)?"
    r"(?:(?P<months>\d+(\.\d+)?)M)?"
    r"(?:(?P<days>\d+(\.\d+)?)D)?"
    r"T?(?:(?P<hours>\d+(\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(\.\d+)?)S)?$"
)


ZERO = timedelta(0)

class TimeZone(tzinfo):
    """ UTC time-zone class. """
    def __init__(self, offset, label):
        tzinfo.__init__(self)
        self._offset = offset
        self._label = label

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._label

    def dst(self, dt):
        return self._offset


UTC = TimeZone(ZERO, "UTC")


def now():
    """ Get current UTC timestamp. """
    return datetime.utcnow()


def today():
    """ Get current UTC date. """
    return now().date()


def to_utc_naive(value):
    """ convert a time-zone aware `datetime` value to a UTC and strip the
    timezone.
    """
    if value.tzinfo:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value


def parse_datetime(value, tz_local=None):
    """ Parse an ISO 8601 date-time value. The parser supports time-zones and
    both long and short formats.
    Raises a `ValueError` if the conversion was not possible.
    """
    if not isinstance(value, datetime):
        for pattern in (RE_ISO_8601_DATETIME_LONG, RE_ISO_8601_DATETIME_SHORT):
            match = pattern.match(value)
            if match:
                break
        else:
            raise ValueError("Invalid date-time input!")

        (
            year, month, day, hour, minute, sec, usec, tzone, tz_hour, tz_min
        ) = match.groups()

        if tzone:
            if tzone == "Z":
                tz_obj = UTC
            else:
                tz_obj = UTC if tzone == "Z" else TimeZone(timedelta(
                    hours=int(tz_hour or 0),
                    minutes=int(tz_hour[0] + (tz_min or '0'))
                ), "%s:%s" % (tz_hour, tz_min or "00"))
        else:
            tz_obj = tz_local

        value = datetime(
            int(year), int(month), int(day or 0),
            int(hour or 0), int(minute or 0), int(sec or 0),
            int(((usec or '') + '000000')[:6]), tz_obj
        )

    # convert time-zone aware date-time to UTC
    return to_utc_naive(value)


def parse_date(value):
    """ Parse an ISO 8601 date.
    Raises a `ValueError` if the conversion was not possible.
    """
    # NOTE: datetime.datetime is inherited from datetime.date!
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return parse_datetime(value).date()


def parse_duration(value):
    """ Parses an ISO 8601 duration string into a python timedelta object.
    Raises a `ValueError` if the conversion was not possible.
    """
    if isinstance(value, timedelta):
        return value

    match = RE_ISO_8601_DURATION.match(value)
    if not match:
        raise ValueError(
            "Could not parse ISO 8601 duration from '%s'." % value
        )
    match = match.groupdict()

    sign = -1 if match['sign'] == "-" else 1
    days = float(match['days'] or 0)
    days += float(match['months'] or 0) * 30  # ?!
    days += float(match['years'] or 0) * 365  # ?!
    fsec = float(match['seconds'] or 0)
    fsec += float(match['minutes'] or 0) * 60
    fsec += float(match['hours'] or 0) * 3600

    if sign < 0:
        raise ValueError("Duration %s must not be negative!" % value)

    return timedelta(days, fsec)


def encode_duration(value):
    """ Encode python timedelta object as ISO 8601 duration string.
    Raises a `ValueError` if the conversion was not possible.
    """
    #NOTE: The months and years are ambiguous and we do not encode them.
    if not isinstance(value, timedelta):
        raise ValueError("Invalid input type!")
    items = []
    if value.days < 0:
        items.append('-')
        value = -value
    items.append('P')
    if value.days != 0:
        items.append('%dD'%value.days)
    elif value.seconds == 0 and value.microseconds == 0:
        items.append('T0S') # zero interval
    if value.seconds != 0 or value.microseconds != 0:
        minutes, seconds = divmod(value.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        items.append('T')
        if hours != 0:
            items.append('%dH'%hours)
        if minutes != 0:
            items.append('%dM'%minutes)
        if value.microseconds != 0:
            items.append("%.6fS"%(seconds+1e-6*value.microseconds))
        elif seconds != 0:
            items.append('%dS'%seconds)
    return "".join(items)


def day2k_to_date(day2k):
    """ Convert integer day number since 2000-01-01 to date as (year, month, day)
    tuple.
    """
    # ref: https://en.wikipedia.org/wiki/Julian_day#Julian_or_Gregorian_calendar_from_Julian_day_number
    # Gregorian date formula applied since 1582-10-15
    # Julian date formula applied until 1582-10-04
    d__ = int(day2k) + 2451545
    f__ = d__ + 1401 # Julian calender
    if d__ > 2299160: # Gregorian calender
        f__ += (((4*d__ + 274277)//146097)*3)//4 - 38
    e__ = 4*f__ + 3
    h__ = 5*((e__ % 1461)//4) + 2
    day = (h__%153)//5 + 1
    month = (h__//153 + 2)%12 + 1
    year = e__//1461 - 4716 + (14 - month)//12
    return year, month, day


def day_fraction_to_time(fraction):
    """ Convert day fraction to to time as (hour, min, sec, usec) tuple. """
    subsec, sec = math.modf(round(fraction * 86400.0, 6)) # round to usec
    sec, usec = int(sec), int(subsec * 1e6)
    min_, sec = sec / 60, sec % 60,
    hour, min_ = min_ / 60, min_ % 60,
    hour, min_ = int(hour), int(min_)   # Added for Python 3
    return hour, min_, sec, usec


def mjd2000_to_datetime(mjd2k):
    """ Convert Modified Julian Date 2000 to `datetime.datetime` object. """
    day2k = math.floor(mjd2k)
    year, month, day = day2k_to_date(day2k)
    hour, min_, sec, usec = day_fraction_to_time(mjd2k - day2k)
    return datetime(year, month, day, hour, min_, sec, usec)


def unix_epoch_to_datetime(ux_epoch):
    """ Convert number of seconds since 1970-01-01 to `datetime.datetime`
    object.
    """
    return datetime.utcfromtimestamp(ux_epoch)


class Timer(object):
    """ Timer class measuring elapsed amount of time.
    """
    def __init__(self):
        self._start = time()

    def restart(self):
        """ Restart the timer. """
        self._start = time()

    @property
    def elapsed_time(self):
        """ Get time time in seconds elapsed since the last timer restart. """
        return time() - self._start
