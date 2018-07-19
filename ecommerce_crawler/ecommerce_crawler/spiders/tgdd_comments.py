# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd

from constants import *


class TgddCommentsSpider(scrapy.Spider):

    """Summary

    Attributes:
        api_pattern (TYPE): Description
        category (str): Description
        comments (TYPE): Description
        name (str): Description
        product_links (TYPE): Description
    """
    name = 'tgdd_comments'
    category = ''
    product_links = list()
    comments = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = TGDD_DTDD['cap_sac']
        self.api = TGDD_DTDD['rating_api']
        self.category_name = self.category['name']

        # load product links
        df = pd.read_csv('data/%s_productlinks.csv' % self.category_name)
        df = df.dropna()
        for index, row in df.iterrows():
            self.product_links.append(
                {'product_id': int(row['product_id']),
                 'product_link': row['product_link']})
        self.logger.info("Total products: %s", len(self.product_links))

        #
        product_info = self.product_links.pop()
        product_id = product_info['product_id']
        product_link = product_info['product_link']
        self.logger.info('MOVE NEXT PRODUCT: product_id=%s, link=%s',
                         product_id, product_link)
        page = 1
        params = {'productid': str(product_id),
                  'page': str(page), 'score': '0'}
        yield scrapy.FormRequest(url=self.api,
                                 formdata=params,
                                 callback=self.parse_comment,
                                 meta={'product_id': product_id, 'page': page},
                                 dont_filter=True)

    def parse_comment(self, response):
        """Summary

        Args:
            response (TYPE): Description

        No Longer Yielded:
            TYPE: Description
        """
        product_id = response.meta['product_id']
        page = response.meta['page']

        self.logger.info('PARSE: product_id=%s, page=%s', product_id, page)

        # parse next page
        if len(response.body) > 0:
            # parse content
            for rating in response.css('li'):
                # get id
                rating_id = rating.css('::attr("id")').extract_first()
                self.logger.debug('rating_id: %s', rating_id)
                if rating_id is not None and rating_id.split('-')[0] == 'r':
                    rating_id = rating_id.split('-')[1]

                    # get number of star
                    stars = len(rating.css('i.iconcom-txtstar').extract())

                    # get comment
                    comment = rating.css('div.rc p i::text').extract_first()

                    self.comments.append(
                        {'product_id': product_id,
                         'comment_id': rating_id,
                         'title': None,
                         'content': comment,
                         'rating': stars,
                         'thank_count': None
                         })
            self.logger.debug('comments: %s', self.comments)
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
            params = {'productid': str(product_id),
                      'page': str(page), 'score': '0'}
            yield scrapy.FormRequest(url=self.api,
                                     formdata=params,
                                     callback=self.parse_comment,
                                     meta={'product_id': product_id,
                                           'page': page},
                                     dont_filter=True)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TgddCommentsSpider, cls).from_crawler(
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
        if len(self.comments) > 0:
            df = pd.DataFrame.from_dict(self.comments)
            file_path = 'data/%s_comments.csv' % self.category_name
            df.to_csv(file_path, index=False, encoding='utf-8',
                      columns=['product_id', 'comment_id', 'title', 'content',
                               'rating', 'thank_count'])
