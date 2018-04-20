"""
Provide some useful functions supporting to Graph API
NOTE: it DOES NOT WORK right now

Attributes:
    logger (TYPE): Description
"""
from urllib.request import urlopen
import time
from datetime import datetime
import pytz
import logging
import calendar

import constant

logger = logging.getLogger(__name__)


# def load_crawled_duration(fb_id):
#     """Summary

#     Args:
#         fb_id (TYPE): Description

#     Returns:
#         TYPE: Description
#     """
#     df = pd.read_csv(os.path.join(BASE_DIR, HISTORY_PATH),
#                      dtype={'fb_id': str})
#     row = df[df['fb_id'] == fb_id].iloc[0]
#     return (df, dateutil.parser.parse(row['min_crawled_time']),
#             dateutil.parser.parse(row['max_crawled_time']))


# def update_crawled_duration(fb_id, crawled_duration, crawled_utctime):
#     """Summary

#     Args:
#         fb_id (TYPE): Description
#         crawled_duration (TYPE): Description
#         crawled_utctime (TYPE): Description

#     Deleted Parameters:
#         page_id (TYPE): Description
#     """
#     df, min_crawled_time, max_crawled_time = load_crawled_duration(fb_id)
#     cond = df['fb_id'] == fb_id
#     df.loc[cond, 'last_crawled_time'] = crawled_utctime
#     if min_crawled_time > crawled_duration[0]:
#         df.loc[cond, 'min_crawled_time'] = crawled_duration[0]
#     if max_crawled_time < crawled_duration[1]:
#         df.loc[cond, 'max_crawled_time'] = crawled_duration[1]
#     df.to_csv(os.path.join(BASE_DIR, HISTORY_PATH), index=False)

def get_group_id(url):
    """Summary

    Args:
        url (TYPE): Description

    Returns:
        TYPE: Description
    """
    items = url.split('/')
    items = [i for i in items if len(i) > 0]
    logger.info('\ngroup id: %s', items[-1].strip())
    return items[-1].strip()


def request_until_succeed(url):
    """Summary

    Args:
        url (TYPE): Description

    Returns:
        TYPE: Description
    """
    success = False
    while success is False:
        try:
            response = urlopen(url)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)
            logger.error('Error for URL %s: %s', url, datetime.now())

    return response.read()


def build_param_string(parameters):
    """
    convert dictionary of parameters into string with format like html query
    key1=value1&key2=value2&key3=value3

    Args:
        parameters (dic): dictionary of paramaters

    Returns:
        string: Description
    """
    return '&'.join(['%s=%s' % (k, str(v)) for k, v in parameters.items()])


def generate_periods(year_from, year_to):
    """Summary

    Args:
        year_from (TYPE): Description
        year_to (TYPE): Description

    Returns:
        TYPE: Description
    """
    periods = []
    vn_tz = pytz.timezone(constant.LOCAL_TIME_ZONE)
    for y in reversed(range(year_from, year_to + 1)):
        for m in reversed(range(1, 13)):
            _, last = calendar.monthrange(y, m)
            first_date = vn_tz.localize(datetime(y, m, 1, 0, 0, 0))
            last_date = vn_tz.localize(datetime(y, m, last, 23, 59, 59))
            if vn_tz.localize(datetime.now()) < first_date:
                continue
            periods.append((first_date, last_date))
    return periods
