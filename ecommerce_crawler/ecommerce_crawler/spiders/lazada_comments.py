# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
import json
from datetime import datetime

from constants import *


class LazadaCommentsSpider(scrapy.Spider):

    """Summary

    Attributes:
        api_pattern (TYPE): Description
        category (str): Description
        comments (TYPE): Description
        name (str): Description
        product_links (TYPE): Description
    """
    name = 'lazada_comments'
    category = ''
    product_links = list()
    comments = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = LAZADA_CATEGORY['dtdd']
        self.category_name = self.category['name']
        df = pd.read_csv('data/%s_productlinks.csv' % self.category_name)
        for index, row in df.iterrows():
            self.product_links.append(
                {'product_id': row['product_id'],
                 'product_link': row['product_link']})
        self.logger.info("Total products: %s", len(self.product_links))

        product_info = self.product_links.pop()
        product_id = product_info['product_id']
        product_link = product_info['product_link']
        self.logger.info('MOVE NEXT PRODUCT: product_id=%s, link=%s',
                         product_id, product_link)
        page = 1
        url = LAZADA_CATEGORY['review_api'] % (product_id, page)
        self.logger.info("URL: %s", url)
        yield scrapy.Request(url, self.parse_comment,
                             meta={'product_id': product_id,
                                   'product_link': product_link,
                                   'page': page},
                             dont_filter=True)

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
        json_comments = jsonresponse['model']['items']
        if json_comments is not None:
            # parse content
            self.logger.debug('url: %s', response.url)
            for comment in json_comments:
                self.comments.append(
                    {'product_id': comment['itemId'],
                     'comment_id': comment['reviewRateId'],
                     'title': comment['reviewTitle'],
                     'content': comment['reviewContent'],
                     'rating': comment['rating'],
                     'thank_count': comment['likeCount']
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
            url = LAZADA_CATEGORY['review_api'] % (product_id, page)
            yield scrapy.Request(url, self.parse_comment,
                                 meta={'product_id': product_id,
                                       'product_link': product_link,
                                       'page': page},
                                 dont_filter=True)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LazadaCommentsSpider, cls).from_crawler(
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
        df.to_csv(file_path, index=False, encoding='utf-8',
                  columns=['product_id', 'comment_id', 'title', 'content',
                           'rating', 'thank_count'])
