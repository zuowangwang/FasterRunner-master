#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import datetime
import json
import time
from collections import Counter

from constance import config

def string2time_stamp(strValue, format=None, is_timestamp=True):

    try:
        if not format:
            format = "%Y%m%d_%H%M%S"
        d = datetime.datetime.strptime(strValue, format)
        if not is_timestamp:
            return d
        t = d.timetuple()
        timeStamp = int(time.mktime(t))
        timeStamp = float(str(timeStamp) + str("%06d" % d.microsecond)) / 1000000
        return timeStamp
    except ValueError as e:
        if not format:
            format = "%Y-%m-%d %H:%M:%S.%f"
        d = datetime.datetime.strptime(strValue, format)
        if not is_timestamp:
            return d
        t = d.timetuple()
        timeStamp = int(time.mktime(t))
        timeStamp = float(str(timeStamp) + str("%06d" % d.microsecond)) / 1000000
        return timeStamp


def gen_summary(obj):
    """
    Statistical data.
    """
    data = []
    for val in obj.values('summary'):
        if not val:
            continue
        summary = json.loads(val['summary'])
        data.append(summary['stat'])
    return dict(sum(map(Counter, data), Counter()))


def get_betweent_date(start, end):
    """
    Get the intermediate period.
    """
    date_list = []
    begin_date = string2time_stamp(start, format="%Y%m%d", is_timestamp=False)
    if end:
        end_date = string2time_stamp(end, format="%Y%m%d", is_timestamp=False)
    else:
        end_date = begin_date + datetime.timedelta(days=config.charts_show_date - 1)
    while begin_date <= end_date:
        # date_str = begin_date.strftime("%Y%m%d")
        date_list.append(begin_date)
        begin_date += datetime.timedelta(days=1)
    return date_list