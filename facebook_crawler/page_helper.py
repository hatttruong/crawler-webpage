"""
Provide some useful functions supporting to Graph API
NOTE: it DOES NOT WORK right now

Attributes:
    ACTIVE_PAGE_PATH (TYPE): Description
    FUL_ACTIVE_PAGE_PATH (TYPE): Description
    HISTORY_PATH (TYPE): Description
    INACTIVE_PAGE_PATH (TYPE): Description
    logger (TYPE): Description


"""
from urllib.request import urlopen
import logging
import json
import pandas as pd
import os

import constant
from dto.fbobject import *
from GA_helper import request_until_succeed, build_param_string
import langdetector


HISTORY_PATH = os.path.join('data', 'crawled_history.csv')
ACTIVE_PAGE_PATH = os.path.join('data', 'active_page_info.csv')
INACTIVE_PAGE_PATH = os.path.join('data', 'inactive_page_info.csv')
FUL_ACTIVE_PAGE_PATH = os.path.join('data', 'full_active_page_info.csv')

logger = logging.getLogger(__name__)


def test_page(page_name):
    """Summary

    Args:
        page_name (TYPE): Description

    """
    # construct the URL string

    node = page_name
    parameters = {'access_token': constant.ACCESS_TOKEN}
    url = '%s/%s/?%s' % (constant.BASE_GRAPH_API, node,
                         build_param_string(parameters))
    logger.debug('url: %s', url)

    # retrieve data
    response = urlopen(url)
    data = response.read().decode('utf-8')
    logger.debug('type of response: %s', str(type(data)))
    data_json = json.loads(data)
    logger.info(data_json)


def get_page_id(page_name):
    """
    find id of FB page from it content. Pattern to find id is:
    - <a href="https://m.me/1000515996721686"... (mobile mode)
    - content="fb://page/?id=1000515996721686 (desktop mode)

    Args:
        page_name (TYPE): Description

    Returns:
        TYPE: Description
    """
    node = page_name
    parameters = {'access_token': constant.ACCESS_TOKEN}
    url = '%s/%s/?%s' % (constant.BASE_GRAPH_API, node,
                         build_param_string(parameters))
    logger.debug('url: %s', url)

    # retrieve data
    response = urlopen(url)
    data = response.read().decode('utf-8')
    logger.debug('type of response: %s', str(type(data)))
    data_json = json.loads(data)
    return data_json['id']


def get_page_info(page_id):
    """
    get page infor by page id

    Args:
        page_id (TYPE): Description
    """
    fields = ['about', 'username', 'name', 'description', 'fan_count',
              'mission', 'talking_about_count', 'company_overview']

    # construct the URL string
    node = page_id
    parameters = {'access_token': constant.ACCESS_TOKEN,
                  'fields': ','.join(fields)}
    url = '%s/%s/?%s' % (constant.BASE_GRAPH_API, node,
                         build_param_string(parameters))
    data = request_until_succeed(url).decode('utf-8')
    page_info = json.loads(data)
    logger.debug('id=%s: %s', page_id, page_info)

    name = ''
    if 'username' in page_info.keys():
        name = page_info['username']
    else:
        name = page_info['name']
    fb_page = FbPage(page_id, name)

    # text fields
    fb_page.name = page_info['name'] if 'name' in page_info.keys() else ''
    fb_page.about = page_info['about'] if 'about' in page_info.keys() else ''
    if 'description' in page_info.keys():
        fb_page.description = page_info['description']
    if 'company_overview' in page_info.keys():
        fb_page.company_overview = page_info['company_overview']
    if 'mission' in page_info.keys():
        fb_page.mission = page_info['mission']

    # number fields
    if 'fan_count' in page_info.keys():
        fb_page.fan_count = page_info['fan_count']
    if 'talking_about_count' in page_info.keys():
        fb_page.talking_about_count = page_info['talking_about_count']

    return fb_page


def get_active_time(page_id):
    """get lastest post

    Args:
        page_id (TYPE): Description
    """
    # construct the URL string
    node = page_id
    edge = 'posts'
    fields = ['created_time', 'type', 'id']
    parameters = {'access_token': constant.ACCESS_TOKEN,
                  'fields': ','.join(fields),
                  'limit': 1}

    url = '%s/%s/%s/?%s' % (constant.BASE_GRAPH_API, node, edge,
                            build_param_string(parameters))
    data = request_until_succeed(url).decode('utf-8')
    posts = json.loads(data)['data']

    if len(posts) > 0:
        post = posts[0]
        last_active_time = dateutil.parser.parse(post['created_time'])
        return last_active_time

    return None


def is_vietnamese_page(page):
    """
    Check page name first, if page name is not Vietnamese, check other fields
    Args:
        page (TYPE): Description

    Returns:
        TYPE: Description
    """
    if langdetector.is_vietnamese(page.name):
        return True

    text = ' '. join([page.about, page.description,
                      page.mission, page.company_overview])
    return langdetector.is_vietnamese(text)


def is_inactive_page(page):
    """Summary

    Args:
        page (FbPage): page instance

    Returns:
        TYPE: Description
    """
    if page.fan_count <= 1000:
        logger.info('page %s has %d fan count', page.name, page.fan_count)
        return True

    # if page.talking_about_count <= 10:
    #     logger.info('page %s has %d talking about',
    #                 page.name, page.talking_about_count)
    #     return True

    # # if the latest post is created less than 3 months, it is inactive
    # vn_tz = pytz.timezone(constant.LOCAL_TIME_ZONE)
    # last_active_time = get_active_time(page.page_id)
    # page.last_active = last_active_time
    # if last_active_time is None or \
    #         (vn_tz.localize(datetime.now()) - last_active_time).days > 90:
    #     logger.info('the last time page %s active is %s',
    #                 page.name, last_active_time)
    #     return True

    return False


def get_liked_pages_by():
    """Summary
    """
    seed_path = os.path.join(constant.BASE_DIR, 'data', 'seed_pages.csv')
    df = pd.read_csv(seed_path, dtype={'page_id': str, 'name': str})
    df = df.fillna('')
    logger.info(df.head())

    ignored_page_ids = set()
    inactive_pages = {}
    active_pages = {}
    for index, row in df.iterrows():
        p_id = row['page_id']
        active_pages[p_id] = get_page_info(p_id)

    while len(active_pages) < 100:
        page_ids = list(active_pages.keys())
        for p_id in page_ids:
            page = active_pages[p_id]

            # construct the URL string
            node = p_id
            edge = 'likes'
            parameters = {'access_token': constant.ACCESS_TOKEN}
            url = '%s/%s/%s/?%s' % (constant.BASE_GRAPH_API, node, edge,
                                    build_param_string(parameters))
            data = request_until_succeed(url).decode('utf-8')
            liked_pages = json.loads(data)['data']
            logger.info('page=%s likes %s', page.name, liked_pages)

            # update liked pages list of current page
            active_pages[p_id].liked_pages = set(
                [l['id'] for l in liked_pages])

            # check if liked page exists in page_info or not
            # in order to add to database if liked page does not exist
            for liked_page in liked_pages:
                liked_id = liked_page['id']
                if liked_id in active_pages.keys():
                    continue
                elif liked_id in inactive_pages.keys():
                    continue
                else:
                    liked_page = get_page_info(liked_id)
                    if is_vietnamese_page(liked_page) is False:
                        ignored_page_ids.add(liked_id)
                        continue

                    if is_inactive_page(liked_page):
                        if liked_id not in inactive_pages.keys():
                            inactive_pages[liked_id] = liked_page
                    else:
                        active_pages[liked_id] = liked_page

        logger.info('TOTAL CRAWLED %d pages', len(active_pages))

    # update active page list
    df = pd.DataFrame.from_records(
        [v.to_dict() for k, v in active_pages.items()])

    # extract full page info
    df.to_csv(os.path.join(constant.BASE_DIR,
                           FUL_ACTIVE_PAGE_PATH), index=False)
    logger.info('export FULL active page info to file: %s',
                FUL_ACTIVE_PAGE_PATH)

    active_file_path = os.path.join(constant.BASE_DIR, ACTIVE_PAGE_PATH)
    df = df[['page_id', 'username', 'name', 'fan_count',
             'talking_about_count', 'last_active', 'liked_pages']]
    df.to_csv(active_file_path, index=False)
    logger.info('export active page info to file: %s', ACTIVE_PAGE_PATH)

    # update inactive page ids
    inactive_file_path = os.path.join(constant.BASE_DIR, INACTIVE_PAGE_PATH)
    df = pd.DataFrame.from_records(
        [v.to_dict() for k, v in inactive_pages.items()])
    df = df[['page_id', 'username']]
    df.to_csv(inactive_file_path, index=False)
    logger.info('export inactive page ids to file: %s', INACTIVE_PAGE_PATH)

    # update ifnored page ids
    ignored_file_path = os.path.join(constant.BASE_DIR, 'ignored_pages.csv')
    df = pd.DataFrame.from_records(
        [{'page_id': p_id} for p_id in ignored_page_ids])
    df.to_csv(ignored_file_path, index=False)
    logger.info('export ignored page ids to file: %s', ignored_file_path)
