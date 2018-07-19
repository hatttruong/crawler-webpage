# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
import json
from datetime import datetime

from constants import *


class TikiCommentsSpider(scrapy.Spider):

    """Summary

    Attributes:
        api_pattern (TYPE): Description
        category (str): Description
        comments (TYPE): Description
        name (str): Description
        product_links (TYPE): Description
    """
    name = 'tiki_comments'
    api_pattern = "https://tiki.vn/api/v2/reviews?product_id=%s&limit=5&sort=score|desc,id|desc,stars|all&include=comments&page=%s&_=%s"
    category = ''
    product_links = list()
    comments = list()

    def get_epoch(self):
        return int(datetime.now().strftime("%s")) * 1000

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = TIKI_CATEGORY['phu_kien_dien_thoai']
        self.category_name = self.category['name']
        self.url = self.category['url']

        df = pd.read_csv('data/%s_productlinks.csv' % self.category_name)
        for index, row in df.iterrows():
            self.product_links.append(
                {'product_id': row['product_id'],
                 'product_link': row['product_link']})
        self.logger.info("Total products: %s", len(self.product_links))

        # https://tiki.vn/api/v2/reviews?product_id=1666621&sort=thank_count|desc&include=comments&page=1&limit=-1&top=true&_=1531495588536
        product_info = self.product_links.pop()
        product_id = product_info['product_id']
        product_link = product_info['product_link']
        self.logger.info('MOVE NEXT PRODUCT: product_id=%s, link=%s',
                         product_id, product_link)
        page = 1
        url = self.api_pattern % (product_id, page, self.get_epoch())
        self.logger.info("URL: %s", url)
        yield scrapy.Request(url, self.parse_comment,
                             meta={'product_id': product_id,
                                   'product_link': product_link,
                                   'page': page})

    def parse_comment(self, response):
        """Summary

        Args:
            response (TYPE): Description

        No Longer Yielded:
            TYPE: Description
        """
        product_id = response.meta['product_id']
        product_link = response.meta['product_link']
        page = response.meta['page']

        self.logger.info('PARSE: product_id=%s, page=%s', product_id, page)
        jsonresponse = json.loads(response.body_as_unicode())

        # parse next page
        if 'data' in jsonresponse.keys() and len(jsonresponse['data']) > 0:
            # parse content
            self.logger.debug('url: %s', response.url)
            self.logger.debug('response.data: %s', jsonresponse['data'])
            for comment in jsonresponse['data']:
                self.comments.append(
                    {'product_id': comment['product_id'],
                     'comment_id': comment['id'],
                     'title': comment['title'].encode('utf-8'),
                     'content': comment['content'].encode('utf-8'),
                     'rating': comment['rating'],
                     'thank_count': comment['thank_count']
                     })
            page += 1
        elif len(self.product_links) > 0:
            # if response is empty, move to next product
            product_info = self.product_links.pop()
            product_id = product_info['product_id']
            product_link = product_info['product_link']
            page = 1
            self.logger.info('Total comments: %s', len(self.comments))
            self.logger.info('MOVE NEXT PRODUCT: product_id=%s, link=%s',
                             product_id, product_link)
        else:
            page = None

        if page:
            url = self.api_pattern % (product_id, page, self.get_epoch())
            yield scrapy.Request(url, self.parse_comment,
                                 meta={'product_id': product_id,
                                       'product_link': product_link,
                                       'page': page})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TikiCommentsSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.logger.info('START CLOSING SPIDER %s', spider.name)
        self.logger.info('Total comments: %s', len(self.comments))
        self.export()

    def export(self):
        """Summary
        """
        self.logger.info('EXPORT DATA TO FILE')
        self.logger.info('crawled %s comments, export data to csv',
                         len(self.comments))
        df = pd.DataFrame.from_dict(self.comments)
        file_path = 'data/%s_comments.csv' % self.category_name
        df.to_csv(file_path, index=False,
                  columns=['product_id', 'comment_id', 'title', 'content',
                           'rating', 'thank_count'])
