# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
from bs4 import BeautifulSoup
from constants import *


class VtaCommentsSpider(scrapy.Spider):

    """Summary

    Attributes:
        api_pattern (TYPE): Description
        category (str): Description
        comments (TYPE): Description
        name (str): Description
        product_links (TYPE): Description
    """
    name = 'vta_comments'
    comment_api = 'https://publicapi.vienthonga.vn/v2/comments?type=list&dg=%s&bl=1&slug=%s'
    category = ''
    product_links = list()
    comments = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = VTA_CATEGORY['phu_kien']
        self.category_name = self.category['name']
        df = pd.read_csv('data/%s_productlinks.csv' % self.category_name)
        for index, row in df.iterrows():
            self.product_links.append(
                {'product_id': row['product_id'],
                 'short_link': row['product_link'].split('/')[-1]
                 }
            )
        self.logger.info("Total products: %s", len(self.product_links))

        product_info = self.product_links.pop()
        product_id = product_info['product_id']
        short_link = product_info['short_link']
        self.logger.info('MOVE NEXT PRODUCT: product_id=%s, link=%s',
                         product_id, short_link)
        page = 1
        url = self.comment_api % (page, short_link)
        self.logger.info("URL: %s", url)
        yield scrapy.Request(url, self.parse_comment,
                             meta={'product_id': product_id,
                                   'short_link': short_link,
                                   'page': page})

    def parse_comment(self, response):
        """Summary

        Args:
            response (TYPE): Description

        No Longer Yielded:
            TYPE: Description
        """
        product_id = response.meta['product_id']
        short_link = response.meta['short_link']
        page = response.meta['page']

        self.logger.info('PARSE: product_id=%s, page=%s', product_id, page)
        response.selector.register_namespace('d', VTA_XML_NAMESPACE)
        has_comments = False
        for i, xml_comment in enumerate(response.xpath(
                '//d:DanhGia/d:DanhGia')):
            # self.logger.debug('comment %s-th', i)
            comment_id = xml_comment.xpath('d:Id/text()').extract_first()
            content = xml_comment.xpath('d:NoiDung/text()').extract_first()
            clean_content = ""
            if content is not None:
                clean_content = BeautifulSoup(content, "html.parser").text
            rating = xml_comment.xpath('d:Rating /text()').extract_first()
            likes = xml_comment.xpath('d:Likes/text()').extract_first()
            self.comments.append(
                {'product_id': product_id,
                 'comment_id': comment_id,
                 'title': '',
                 'content': clean_content,
                 'rating': rating,
                 'thank_count': 0 if likes is None else int(likes)})
            has_comments = True

        if has_comments:
            page += 1
        elif len(self.product_links) > 0:
            # if response is empty, move to next product
            product_info = self.product_links.pop()
            product_id = product_info['product_id']
            short_link = product_info['short_link']
            page = 1
            self.logger.info('Total comments: %s', len(self.comments))
            self.logger.info('MOVE NEXT PRODUCT: product_id=%s, short_link=%s',
                             product_id, short_link)
        else:
            page = None

        if page:
            # crawl next url
            url = self.comment_api % (page, short_link)
            yield scrapy.Request(url, self.parse_comment,
                                 meta={'product_id': product_id,
                                       'short_link': short_link,
                                       'page': page})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(VtaCommentsSpider, cls).from_crawler(
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
