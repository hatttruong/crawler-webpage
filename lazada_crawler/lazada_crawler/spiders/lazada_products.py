# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
import pandas as pd
from scrapy import signals
from constants import *
from bs4 import BeautifulSoup
import string
from scrapy_splash import SplashRequest

lua_script = """
function main(splash)
    local num_scrolls = 10
    local scroll_delay = 1.0

    local scroll_to = splash:jsfunc("window.scrollTo")
    local get_body_height = splash:jsfunc(
        "function() {return document.body.scrollHeight;}"
    )
    assert(splash:go(splash.args.url))
    splash:wait(splash.args.wait)

    for _ = 1, num_scrolls do
        scroll_to(0, get_body_height())
        splash:wait(scroll_delay)
    end
    return splash:html()
end
"""


class MySpider(scrapy.Spider):
    name = "jsscraper"
    product_ids = list()
    start_urls = [
        "https://www.lazada.vn/dien-thoai-di-dong/?page=" + str(i)
        for i in range(10)]

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url=url, callback=self.parse,
                                endpoint='execute',
                                args={'wait': 2, 'lua_source': lua_script},)

    def parse(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        # extract product links
        df = pd.DataFrame.from_dict([{"data": response.body}])
        file_path = 'debug_%s.csv' % (response.url.split('?')[1])
        df.to_csv(file_path, index=False, encoding='utf-8')

        items = response.xpath('//div[@data-qa-locator="product-item"]')
        for item in items:
            product_id = item.xpath('@data-item-id').extract_first()
            self.logger.info('id=%s', product_id)
            self.logger.info('url=%s',
                             item.xpath('a[@age="0"]/@href').extract_first())

            if product_id in self.product_ids:
                self.logger.info('DUPLICATED!!!')
            else:
                self.product_ids.append(product_id)
                self.logger.info('TOTAL: %s', len(self.product_ids))


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
    dict_product_links = dict()
    dict_products = dict()
    # test_response = list()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = LAZADA_CATEGORY['dtdd']
        self.category_name = self.category['name']
        page_id = 10
        url = self.category['url'] + str(page_id)
        self.logger.info("URL: %s", url)
        endpoint_page = 'render_%s.html' % page_id
        yield SplashRequest(url=url, callback=self.parse_links,
                            endpoint=endpoint_page,
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
        page_id = response.meta['page_id']

        # extract product links
        # df = pd.DataFrame.from_dict([{"data": response.body}])
        # file_path = '%s_debug_%s.csv' % (self.category_name, page_id)
        # df.to_csv(file_path, index=False, encoding='utf-8')

        items = response.xpath('//div[@data-qa-locator="product-item"]')
        for item in items:
            product_id = item.xpath('@data-item-id').extract_first()
            product_link = item.xpath('//a[@age="0"]/@href').extract_first()
            if product_id is not None and product_link is not None:
                product_link = product_link.split('?')[0]
                if product_id not in self.dict_product_links.keys():
                    self.dict_product_links[product_id] = product_link

        self.logger.info('Total product links: %s',
                         len(self.dict_product_links))

        if len(items) > 0:
            # get next page
            page_id += 1
            url = self.category['url'] + str(page_id)
            self.logger.info("URL: %s", url)
            endpoint_page = 'render_%s.html' % page_id
            yield SplashRequest(url=url, callback=self.parse_links,
                                endpoint=endpoint_page,
                                meta={'page_id': page_id})
        else:
            self.logger.info('Total product: %s',
                             len(self.dict_product_links))

            # extract product detail, start with first url
            remaining_product_ids = list(self.dict_product_links.keys())
            next_product_id = remaining_product_ids.pop()
            self.logger.info('PARSE NEXT: url=%s',
                             self.dict_product_links[next_product_id])

            yield scrapy.Request(
                self.dict_product_links[next_product_id],
                self.parse_detail,
                meta={'product_id': next_product_id,
                      'remaining_products': remaining_product_ids},
                dont_filter=True)

    def parse_detail(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        product_id = response.meta['product_id']
        remaining_product_ids = response.meta['remaining_product_ids']
        self.logger.info('REMAINING: %s', len(remaining_product_ids))

        if product_id not in self.dict_products.keys():
            # parse top features
            top_features = list()
            elements = response.css(
                "div.pdp-product-highlights ul li::text").extract()
            for f in elements:
                clean_f = BeautifulSoup(f, "html.parser").text
                top_features.append(clean_f.strip())
            self.logger.debug("top_features: %s", top_features)

            # parse detail features
            features = response.css("ul.specification-keys li")
            feature_values = dict()
            for f in features:
                f_name = f.css('span.key-title::text').extract_first()
                f_value = f.css('div.key-value::text').extract_first()
                if f_name is not None and f_value is not None:
                    feature_values[f_name.strip()] = f_value.strip()
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
            self.logger.info('Product: %s exists', product_id)

        # now do next schedule items
        if len(remaining_product_ids) > 0:
            next_product_id = remaining_product_ids.pop()
            self.logger.info('PARSE NEXT: id=%s', next_product_id)
            self.logger.info('PARSE NEXT: url=%s',
                             self.dict_product_links[next_product_id])

            yield scrapy.Request(
                self.dict_product_links[next_product_id],
                self.parse_detail,
                meta={'product_id': next_product_id,
                      'remaining_product_ids': remaining_product_ids},
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
            len(self.dict_product_links), len(self.dict_products))
        if len(self.dict_product_links) > 0:
            df = pd.DataFrame.from_dict(
                [{'product_id': k, 'product_link': self.dict_product_links[k]}
                 for k in self.dict_product_links.keys()])
            file_path = 'data/%s_productlinks.csv' % self.category_name
            df.to_csv(file_path, index=False,
                      columns=['product_id', 'product_link'])

        if len(self.dict_products) > 0:
            df = pd.DataFrame.from_dict(self.dict_products.values())
            file_path = 'data/%s_products.csv' % self.category_name
            df.to_csv(
                file_path, index=False, encoding='utf-8',
                columns=['product_id', 'top_features', 'features', 'content'])
