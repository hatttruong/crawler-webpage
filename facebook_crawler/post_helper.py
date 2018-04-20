"""
Provide some useful functions supporting to Graph API
NOTE: it DOES NOT WORK right now

Attributes:
    logger (TYPE): Description

"""
from datetime import datetime
import pytz
import logging
import json
import pandas as pd
import os
import calendar

import constant
from dto.fbobject import *
from GA_helper import generate_periods
from GA_helper import request_until_succeed
from GA_helper import build_param_string


logger = logging.getLogger(__name__)


def get_current_posts(page_name, output_path):
    """
    crawl posts in the current month

    Args:
        page_name (TYPE): Description
        output_path (TYPE): Description
    """
    y = datetime.now().year
    m = datetime.now().month
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    _, last = calendar.monthrange(y, m)
    first_date = vn_tz.localize(datetime(y, m, 1, 0, 0, 0))
    last_date = vn_tz.localize(datetime(y, m, last, 23, 59, 59))
    get_posts_by_periods(page_name, output_path, [(first_date, last_date)])


def get_history_posts(page_name, output_path, year_from, year_to):
    """
    get posts in the given period

    Args:
        page_name (TYPE): Description
        output_path (TYPE): Description
        year_from (TYPE): Description
        year_to (TYPE): Description
    """
    # generate period from year_from and year_to
    periods = generate_periods(year_from, year_to)
    get_posts_by_periods(page_name, output_path, periods)


def get_posts_by_periods(page_name, output_path, periods):
    """Summary

    Args:
        page_name (TYPE): Description
        output_path (TYPE): Description
        periods (TYPE): Description
    """
    total_posts = 0
    page_id = get_page_id(page_name=page_name)

    # construct the URL string
    node = page_name
    edge = 'posts'
    fields = ['message', 'link', 'created_time', 'type', 'id',
              'comments.limit(1).summary(true)',
              'reactions.type(LIKE).limit(0).summary(1).as(like)',
              'reactions.type(LOVE).limit(0).summary(1).as(love)',
              'reactions.type(HAHA).limit(0).summary(1).as(haha)',
              'reactions.type(WOW).limit(0).summary(1).as(wow)',
              'reactions.type(SAD).limit(0).summary(1).as(sad)',
              'reactions.type(ANGRY).limit(0).summary(1).as(angry)'
              ]
    parameters = {'access_token': constant.ACCESS_TOKEN,
                  'fields': ','.join(fields),
                  'limit': 100}

    url = '%s/%s/%s/?%s' % (constant.BASE_GRAPH_API, node, edge,
                            build_param_string(parameters))

    no_page_to_load = False
    for period in periods:
        fb_posts = []
        crawled_utctime = datetime.utcnow()
        jump_to_prev_period = False
        while url is not None:
            logger.info('crawl url: %s' % url)
            # retrieve data
            data = request_until_succeed(url).decode('utf-8')
            posts = json.loads(data)['data']
            for p in posts:
                p['crawled_utctime'] = crawled_utctime
                try:
                    post_obj = FbPost(page_id, p)
                    logger.debug(post_obj.__dict__)

                    if post_obj.created_time > period[1]:
                        logger.info(
                            'crawled posts is newer than period, move next>>')
                        continue

                    if post_obj.created_time < period[0]:
                        jump_to_prev_period = True
                        break
                    fb_posts.append(post_obj)
                except Exception as e:
                    logger.error(e)
                    logger.error('ERROR when parsing data_json=%s', p)

            if jump_to_prev_period:
                export_posts_to_file(fb_posts, page_id, period[0], output_path)
                break

            # get next page result
            url = None
            paging = json.loads(data)['paging']
            if 'next' in paging.keys():
                url = paging['next']
            else:
                logger.info('there is no more page to load')
                no_page_to_load = True
                export_posts_to_file(fb_posts, page_id, period[0], output_path)
                break

        total_posts += len(fb_posts)
        logger.info('There are %d posts in time %s', len(fb_posts), period[0])

        if no_page_to_load:
            break

    logger.info('There are %d posts in from %s to %s.',
                total_posts, periods[-1][0], periods[0][1])


def export_posts_to_file(fb_posts, fb_id, start_date, output_path):
    """Summary

    Args:
        fb_posts (TYPE): Description
        fb_id (TYPE): Description
        start_date (TYPE): Description
        output_path (TYPE): Description

    Returns:
        TYPE: Description
    """
    # export data to csv
    if len(fb_posts) == 0:
        return

    df = pd.DataFrame.from_records([p.to_dict() for p in fb_posts])
    file_name = '%s_post_%s.csv' % (
        fb_id, start_date.strftime(constant.STR_DATE_FORMAT))
    df.to_csv(os.path.join(output_path, file_name), index=False)
    logger.info('export crawled data to file: %s', file_name)
