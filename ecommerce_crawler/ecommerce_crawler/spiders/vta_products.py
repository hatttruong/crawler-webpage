# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy import signals
import pandas as pd
from bs4 import BeautifulSoup
from constants import *
from helper import *


class VtaProductsSpider(scrapy.Spider):

    """
    VienthongA provide API to get data directly
    Increase page id until it does not return result anymore.

    Attributes:
        category (str): Description
        name (str): Description
        product_links (TYPE): Description
        products (TYPE): Description
    """

    name = 'vta_products'
    category = ''
    product_links = list()
    products = dict()
    comments = list()
    vta_host = 'https://vienthonga.vn'
    features_api = 'https://publicapi.vienthonga.vn/v2/products?type=detail-feature&productids=%s'
    detail_api = 'https://publicapi.vienthonga.vn/v2/products?type=detail-description&productids=%s'

    def get_url(self, page_id):
        url = self.category['url']
        if self.category_name.find('phu_kien') < 0:
            url = self.category['url'] % page_id
        self.logger.info("URL: %s", url)
        return url

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = VTA_CATEGORY['phu_kien']
        self.category_name = self.category['name']

        page_id = 1
        yield scrapy.Request(url=self.get_url(page_id),
                             callback=self.parse_links,
                             meta={'page_id': page_id})

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
        page_id = response.meta['page_id']

        content = response.body_as_unicode().strip()
        finish_crawl_links = True
        if len(content) > 0:
            # self.logger.debug('PARSE page=%s: %s', page_id, content)
            links = response.css('a.product-link::attr(href)').extract()
            for product_link in links:
                if product_link is None:
                    continue
                # url
                product_link = self.vta_host + product_link
                self.product_links.append(
                    {'product_link': product_link})
                self.logger.debug("Product Link: %s", product_link)

            self.logger.info('Total product links: %s',
                             len(self.product_links))

            # get next page if it is not phu_kien
            if self.category_name.find('phu_kien') < 0:
                finish_crawl_links = False
                page_id += 1
                yield scrapy.Request(url=self.get_url(page_id),
                                     callback=self.parse_links,
                                     meta={'page_id': page_id}
                                     )
        if finish_crawl_links:
            self.logger.info('Total product links in final: %s',
                             len(self.product_links))

            # extract product id with first url
            remaining_products = list(self.product_links)
            self.product_links = list()
            next_product = remaining_products.pop()
            yield scrapy.Request(
                next_product['product_link'],
                self.parse_id,
                meta={'cur_product_link': next_product['product_link'],
                      'remaining_products': remaining_products})

    def parse_id(self, response):
        product_link = response.meta['cur_product_link']
        remaining_products = response.meta['remaining_products']
        self.logger.info('REMAINING: %s', len(remaining_products))

        # parse product id
        product_id = response.css(
            "input#productId::attr(value)").extract_first()
        self.product_links.append(
            {'product_id': product_id, 'product_link': product_link})
        self.logger.info('product_id=%s', product_id)

        # now do next schedule items
        if len(remaining_products) > 0:
            next_product = remaining_products.pop()
            self.logger.info('PARSE NEXT: product_link=%s',
                             next_product['product_link'])
            yield scrapy.Request(
                next_product['product_link'],
                self.parse_id,
                meta={'cur_product_link': next_product['product_link'],
                      'remaining_products': remaining_products})
        else:
            self.logger.info('Total product links after parsing id: %s',
                             len(self.product_links))

            # parse detail
            remaining_requests = list()
            for product in self.product_links:
                # request features, detail, comment
                remaining_requests.append(
                    {'url': self.features_api % product['product_id'],
                     'type': 'features',
                     'product_id': product['product_id']})

                remaining_requests.append(
                    {'url': self.detail_api % product['product_id'],
                     'type': 'detail',
                     'product_id': product['product_id']})

                # initial products
                self.products[product['product_id']] = {
                    'product_id': product['product_id'],
                    'top_features': ''}

            self.logger.info('Total request: %s', len(remaining_requests))

            next_request = remaining_requests.pop()
            self.logger.info('PARSE NEXT: product_id=%s, url=%s',
                             next_request['product_id'],
                             next_request['url'])
            yield scrapy.Request(
                next_request['url'],
                self.parse_detail,
                meta={'cur_request': next_request,
                      'remaining_requests': remaining_requests})

    def parse_detail(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        cur_request = response.meta['cur_request']
        request_type = cur_request['type']
        product_id = cur_request['product_id']
        remaining_requests = response.meta['remaining_requests']
        self.logger.info('REMAINING: %s', len(remaining_requests))
        self.logger.debug('PARSE DETAIL: product_id=%s, type=%s',
                          product_id, request_type)
        self.logger.debug('url: %s', response.url)

        if request_type == 'features':
            # parse detail features
            response.selector.register_namespace('d', VTA_XML_NAMESPACE)
            feature_values = dict()
            for i, f in enumerate(response.xpath('//d:ProductFeatureInfo')):
                # self.logger.debug('extract feature: %s', i)
                f_name = f.xpath(
                    'd:ProductFeatureDescription/text()').extract_first()
                f_value = f.xpath('d:Value/text()').extract_first()
                if f_value is None:
                    f_value = f.xpath(
                        'd:ProductFeatureVariantDescription/text()').extract_first()
                clean_value = ""
                if f_value is not None:
                    clean_value = BeautifulSoup(f_value, "html.parser").text
                feature_values[f_name] = clean_feature(clean_value)
            self.products[product_id]['features'] = feature_values
            # self.logger.debug("DETAIL FEATURES: %s", feature_values)

        elif request_type == 'detail':
            # parse content
            response.selector.register_namespace('d', VTA_XML_NAMESPACE)
            content = response.xpath(
                '//d:HtmlFullDescription//text()').extract_first()
            self.logger.debug(content)
            if content is not None:
                clean_content = BeautifulSoup(content, "html.parser").text
                self.products[product_id]['content'] = clean_content
                self.logger.debug("CLEAN CONTENT: %s", clean_content)
            else:
                self.products[product_id]['content'] = ""

        # now do next schedule items
        if len(remaining_requests) > 0:
            next_request = remaining_requests.pop()
            self.logger.info('PARSE NEXT: product_id=%s, type=%s',
                             next_request['product_id'],
                             next_request['type'])
            self.logger.debug('url=%s', next_request['url'])
            yield scrapy.Request(
                next_request['url'],
                self.parse_detail,
                meta={'cur_request': next_request,
                      'remaining_requests': remaining_requests})

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
        spider = super(VtaProductsSpider, cls).from_crawler(
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

        df = pd.DataFrame.from_dict(self.products.values())
        file_path = 'data/%s_products.csv' % self.category_name
        df.to_csv(
            file_path, index=False, encoding='utf-8',
            columns=['product_id', 'top_features', 'features', 'content'])
