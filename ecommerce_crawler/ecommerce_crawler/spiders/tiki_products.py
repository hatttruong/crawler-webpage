# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
import string

from constants import *
from helper import *


class TikiProductsSpider(scrapy.Spider):

    """Summary

    Attributes:
        category (str): Description
        name (str): Description
        product_links (TYPE): Description
        products (TYPE): Description
    """
    name = 'tiki_products'
    category = ''
    product_links = list()
    products = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = TIKI_CATEGORY['phu_kien_dien_thoai']
        self.category_name = self.category['name']
        self.url = self.category['url']
        self.logger.info("URL: %s", self.url)
        yield scrapy.Request(url=self.url, callback=self.parse_links)

    def parse_links(self, response):
        """Summary

        Args:
            response (TYPE): Description

        No Longer Yielded:
            TYPE: Description

        Yields:
            TYPE: Description
        """
        # extract product links
        self.logger.info('PARSE STEP')
        links = response.css(
            "div.product-box-list div.product-item a")
        for link in links:
            product_id = link.css('::attr(data-id)').extract_first()
            product_link = link.css('::attr(href)').extract_first()
            if product_link is None or product_id is None:
                continue
            self.product_links.append(
                {'product_id': product_id, 'product_link': product_link})
            self.logger.debug("Product Id: %s", product_id)
            self.logger.debug("Product Link: %s", product_link)

        self.logger.info('Total product links: %s', len(self.product_links))

        # get next page
        # <li><a rel="next" class="next"
        # href="/dien-thoai-may-tinh-bang/c1789?page=2">
        # <i class="ico ico-arrow-next"></i></a></li>
        NEXT_PAGE_SELECTOR = 'li a.next::attr(href)'
        next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()
        self.logger.info("next_page: %s", next_page)
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_links
            )
        else:
            self.logger.info('Total product links (2): %s',
                             len(self.product_links))

            # extract product detail, start with first url
            remaining_products = list(self.product_links)
            next_product = remaining_products.pop()
            yield scrapy.Request(
                next_product['product_link'],
                self.parse_detail,
                meta={'cur_product_id': next_product['product_id'],
                      'remaining_products': remaining_products})

    def parse_detail(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        product_id = response.meta['cur_product_id']
        remaining_products = response.meta['remaining_products']
        self.logger.info('REMAINING: %s', len(remaining_products))

        self.logger.debug('PARSE DETAIL: product_id=%s, body=%s',
                          product_id, response.body_as_unicode()[:10])

        # parse top features
        top_features = response.css("div.top-feature-item p::text").extract()
        top_features = ';'.join([f.replace("'", "") for f in top_features])
        self.logger.debug("TOP FEATURES: %s", top_features)

        # parse detail features
        features = response.css("table#chi-tiet tbody tr")
        feature_values = dict()
        for f in features:
            temp = f.css('td::text').extract()
            if len(temp) >= 2:
                f_name = str.strip(temp[0].encode('utf-8'))
                f_value = clean_feature(temp[1].encode('utf-8'))

                # NOTE: remove ' in order to parse data when read file
                f_value = f_value.replace("'", "")
                feature_values[f_name] = f_value
        self.logger.debug("DETAIL FEATURES: %s", feature_values)

        # parse content
        content_elements = response.css("div#gioi-thieu *::text").extract()
        self.logger.debug("CONTENT")
        content = []
        for element in content_elements:
            element = str.strip(element.encode('utf-8'))
            if len(element) > 0:
                if element[-1] not in string.punctuation:
                    element = element + '.'
                content.append(element)

        self.products.append({'product_id': product_id,
                              'top_features': top_features,
                              'features': feature_values,
                              'content': ' '.join(content)})
        self.logger.debug(self.products)

        # now do next schedule items
        if remaining_products:
            next_product = remaining_products.pop()
            self.logger.info('PARSE NEXT: product_id=%s',
                             next_product['product_id'])
            yield scrapy.Request(
                next_product['product_link'],
                self.parse_detail,
                meta={'cur_product_id': next_product['product_id'],
                      'remaining_products': remaining_products})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Summary

        Args:
            crawler (TYPE): Description
            *args: Description
            **kwargs: Description

        Returns:
            TYPE: Description
        """
        spider = super(TikiProductsSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """Summary

        Args:
            spider (TYPE): Description
        """
        self.logger.info('START CLOSING SPIDER %s', spider.name)
        self.logger.info('Total detail products: %s', len(self.products))
        self.export()

    def export(self):
        """Summary
        """
        self.logger.info('EXPORT DATA TO FILE')
        self.logger.info(
            'crawled %s links, %s detail products, export data to csv',
            len(self.product_links), len(self.products))
        df = pd.DataFrame.from_dict(self.product_links)
        file_path = 'data/%s_productlinks.csv' % self.category_name
        df.to_csv(file_path, index=False,
                  columns=['product_id', 'product_link'])

        df = pd.DataFrame.from_dict(self.products)
        file_path = 'data/%s_products.csv' % self.category_name
        df.to_csv(
            file_path, index=False, encoding='utf-8',
            columns=['product_id', 'top_features', 'features', 'content'])
