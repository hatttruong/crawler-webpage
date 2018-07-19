# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
import json
from bs4 import BeautifulSoup
import string


from constants import *
from helper import *


class LazadaProductsSpider(scrapy.Spider):

    """Summary

    Attributes:
        category (str): Description
        name (str): Description
        product_links (TYPE): Description
        products (TYPE): Description
    """
    name = 'lazada_products'
    category = ''
    product_links = list()
    products = list()
    dict_products = dict()
    # test_response = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = LAZADA_CATEGORY['dtdd']
        self.category_name = self.category['name']
        page_id = 1
        url = self.category['url'] + str(page_id)
        self.logger.info("URL: %s", url)
        yield scrapy.Request(url=url,
                             headers={},
                             callback=self.parse_links,
                             meta={'page_id': page_id},
                             dont_filter=True)

    def parse_links(self, response):
        """Summary

        Args:
            response (TYPE): Description

        No Longer Yielded:
            TYPE: Description

        Yields:
            TYPE: Description
        """
        page_id = response.meta['page_id']
        # extract product links
        df = pd.DataFrame.from_dict([{"data": response.body}])
        file_path = '%s_debug_%s.csv' % (self.category_name, page_id)
        df.to_csv(file_path, index=False, encoding='utf-8')

        jsonresponse = json.loads(response.body)
        if len(jsonresponse['mods']['listItems']) > 0:
            items = jsonresponse['mods']['listItems']
            for item in items:
                product_link = 'https:' + item['productUrl']
                product_id = item['itemId']
                if product_id not in [p['product_id'] for p in self.products]:
                    self.products.append(
                        {'product_id': product_id,
                         'product_link': product_link})
            self.logger.info('Total product links: %s',
                             len(self.products))

            # get next page
            page_id += 1
            url = self.category['url'] + str(page_id)
            self.logger.info("next_page: %s", url)
            yield scrapy.Request(url=url,
                                 callback=self.parse_links,
                                 meta={'page_id': page_id})
        else:
            self.logger.info('Total distinct product: %s',
                             len(self.products))

            # extract product detail, start with first url
            remaining_products = list(self.products)
            next_product = remaining_products.pop()
            self.logger.info('PARSE NEXT: url=%s',
                             next_product['product_link'])

            yield scrapy.Request(
                next_product['product_link'],
                self.parse_detail,
                meta={'product_link': next_product['product_link'],
                      'product_id': next_product['product_id'],
                      'remaining_products': remaining_products},
                dont_filter=True)

    def parse_detail(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        product_id = response.meta['product_id']
        remaining_products = response.meta['remaining_products']
        self.logger.info('REMAINING: %s', len(remaining_products))

        if product_id not in self.dict_products.keys():
            # parse top features
            top_features = list()
            elements = response.css(
                "div.pdp-product-highlights ul li::text").extract()
            for f in elements:
                clean_f = BeautifulSoup(f, "html.parser").text
                top_features.append(clean_f.strip().replace("'", ""))
            self.logger.debug("top_features: %s", top_features)

            # parse detail features
            features = response.css("ul.specification-keys li")
            feature_values = dict()
            for f in features:
                f_name = f.css('span.key-title::text').extract_first()
                f_value = f.css('div.key-value::text').extract_first()
                if f_name is not None and f_value is not None:
                    value = clean_feature(f_value)
                    feature_values[f_name.strip()] = value
            self.logger.debug("DETAIL FEATURES: %s", feature_values)

            # parse content
            content_elements = response.css(
                "div.detail-content *::text").extract()
            self.logger.debug("CONTENT")
            content = []
            for element in content_elements:
                element = str.strip(element.encode('utf-8'))
                if len(element) > 0:
                    if element[-1] not in string.punctuation:
                        element = element + '.'
                    content.append(element)

            self.dict_products[product_id] = {'product_id': product_id,
                                              'top_features': top_features,
                                              'features': feature_values,
                                              'content': ' '.join(content)}
            self.logger.info('Total product: %s', len(self.dict_products))
        else:
            elf.logger.info('Product: %s exists', product_id)

        # now do next schedule items
        if len(remaining_products) > 0:
            next_product = remaining_products.pop()
            self.logger.info('PARSE NEXT: url=%s', next_product)
            self.logger.info('PARSE NEXT: url=%s',
                             next_product['product_link'])

            yield scrapy.Request(
                next_product['product_link'],
                self.parse_detail,
                meta={'product_link': next_product['product_link'],
                      'product_id': next_product['product_id'],
                      'remaining_products': remaining_products},
                dont_filter=True)

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
        spider = super(LazadaProductsSpider, cls).from_crawler(
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
        self.logger.info('Total detail products: %s', len(self.dict_products))
        self.export()

    def export(self):
        """Summary
        """
        self.logger.info('EXPORT DATA TO FILE')
        self.logger.info(
            'crawled %s links, %s detail products, export data to csv',
            len(self.product_links), len(self.dict_products))
        if len(self.product_links) > 0:
            df = pd.DataFrame.from_dict(self.product_links)
            file_path = 'data/%s_productlinks.csv' % self.category_name
            df.to_csv(file_path, index=False,
                      columns=['product_id', 'product_link'])

        if len(self.dict_products) > 0:
            df = pd.DataFrame.from_dict(self.dict_products.values())
            file_path = 'data/%s_products.csv' % self.category_name
            df.to_csv(
                file_path, index=False, encoding='utf-8',
                columns=['product_id', 'top_features', 'features', 'content'])
