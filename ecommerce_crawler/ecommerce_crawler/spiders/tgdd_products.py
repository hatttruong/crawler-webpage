# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy.selector import Selector
from scrapy import signals
import pandas as pd
import json
import string

from constants import *
from helper import *


class TgddProductsSpider(scrapy.Spider):

    """Summary

    Attributes:
        category (str): Description
        name (str): Description
        product_links (TYPE): Description
        products (TYPE): Description
    """
    name = 'tgdd_products'
    tgdd_host = 'https://www.thegioididong.com'
    category = ''
    product_links = list()
    dict_products = dict()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        self.category = TGDD_DTDD['chuot']
        self.api = self.category['api']
        self.params = self.category['params']
        self.feature_api = TGDD_DTDD['feature_api']
        self.category_name = self.category['name']
        self.logger.info("URL: %s", self.api)

        params = self.params.copy()
        yield scrapy.FormRequest(url=self.api,
                                 formdata=params,
                                 callback=self.parse_links,
                                 meta={'page_id': 0})

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
        self.logger.info('parse page %s', page_id)

        # check empty result
        if response.body.find('Không tìm thấy kết quả nào phù hợp') < 0:
            # if len(self.product_links) < 10:
            # extract product links
            links = response.css("li a::attr(href)").extract()
            for l in links:
                if l.find('them-vao-gio-hang') >= 0:
                    continue
                self.product_links.append(self.tgdd_host + l)
            self.logger.info('Total product links: %s',
                             len(self.product_links))

            # extract next page
            params = self.params.copy()
            page_id += 1
            if 'PageIndex' in params.keys():
                params['PageIndex'] = str(page_id)
            else:
                params['Index'] = str(page_id)
            yield scrapy.FormRequest(url=self.api,
                                     formdata=params,
                                     callback=self.parse_links,
                                     meta={'page_id': page_id})
        else:
            # extract product
            self.logger.info('Total product links in final: %s',
                             len(self.product_links))

            # extract product id with first url
            remaining_product_links = list(self.product_links)
            self.product_links = list()
            product_link = remaining_product_links.pop()
            self.logger.info('Parse detail url: %s', product_link)
            yield scrapy.Request(
                product_link,
                self.parse_detail,
                meta={'cur_product_link': product_link,
                      'remaining_product_links': remaining_product_links})

    def parse_detail(self, response):
        self.logger.info('test_parse_detail')
        product_link = response.meta['cur_product_link']
        remaining_product_links = response.meta['remaining_product_links']
        self.logger.info('REMAINING product links: %s',
                         len(remaining_product_links))

        # parse product id
        # <a href="/them-vao-gio-hang?ProductId=54318" class="buy_now">...
        giohang_link = response.css('a.buy_now::attr(href)').extract_first()
        product_id = None
        for p in giohang_link.split('?')[1].split('&'):
            param = p.split('=')[0].encode('utf-8')
            if str.lower(param) == 'productid':
                product_id = p.split('=')[1]
        self.logger.info('product_id=%s', product_id)

        if product_id is not None:
            self.product_links.append(
                {'product_id': product_id, 'product_link': product_link})
            self.dict_products[product_id] = {'product_id': product_id,
                                              'top_features': '',
                                              'features': None,
                                              'content': None}

            # if there is button viewparameterfull, features will be extract by
            # calling another request
            viewfull_button = response.css(
                'button.viewparameterfull::attr(style)').extract_first()
            self.logger.info('viewfull_button=%s', viewfull_button)
            if viewfull_button is None or len(viewfull_button) == '':
                # parse features here
                self.logger.info(
                    'product_id=%s has no button viewfulll', product_id)
                feature_values = dict()
                for f in response.css('div.tableparameter ul.parameter li'):
                    f_name = None
                    for name in f.css('span *::text').extract():
                        if len(name.strip()) > 0:
                            f_name = name.strip(' :')

                    f_values = []
                    for v in f.css('div *::text').extract():
                        v = clean_feature(v)
                        if len(v) > 0 and v not in string.punctuation:
                            f_values.append(v)

                    if f_name is not None and len(f_values) > 0:
                        self.logger.debug('%s: %s', f_name,
                                          ', '.join(f_values))
                        feature_values[f_name] = ', '.join(f_values)

                self.dict_products[product_id]['features'] = feature_values

            # parse content
            content_elements = response.css(
                'div.boxArticle article.area_article *::text').extract()
            content = []
            for element in content_elements:
                element = str.strip(element.encode('utf-8'))
                if len(element) > 0:
                    if element[-1] not in string.punctuation:
                        element = element + '.'
                    content.append(element)
            # CHEAT: remove "Không hài lòng bài viết. Hãy để lại thông tin để
            # được hỗ trợ khi cần thiết (Không bắt buộc): Anh. Chị. Gửi góp ý.
            # Cam kết bảo mật thông tin cá nhân."
            redundant_text = "Không hài lòng bài viết. Hãy để lại thông tin để được hỗ trợ khi cần thiết (Không bắt buộc): Anh. Chị. Gửi góp ý. Cam kết bảo mật thông tin cá nhân."
            content = ' '.join(content)
            content = content.replace(redundant_text, "")
            self.dict_products[product_id]['content'] = ' '.join(content)

        # now do next schedule items
        if len(remaining_product_links) > 0:
            product_link = remaining_product_links.pop()
            self.logger.info('PARSE NEXT: product_link=%s', product_link)
            yield scrapy.Request(
                product_link,
                self.parse_detail,
                meta={'cur_product_link': product_link,
                      'remaining_product_links': remaining_product_links})
        else:
            # parse detail features for products having too many features
            product_without_features = []
            for k in self.dict_products.keys():
                if self.dict_products[k]['features'] is None:
                    product_without_features.append(k)

            if len(product_without_features) > 0:
                next_product_id = product_without_features.pop()
                self.logger.info(
                    'PARSE FEATURES OF product_id=%s', next_product_id)
                yield scrapy.FormRequest(
                    url=self.feature_api,
                    formdata={'productID': str(next_product_id)},
                    callback=self.parse_features,
                    meta={'product_id': next_product_id,
                          'product_without_features': product_without_features})

    def parse_features(self, response):
        product_id = response.meta['product_id']
        product_without_features = response.meta['product_without_features']

        # parse detail feature
        jsonresponse = json.loads(response.body_as_unicode())
        if len(jsonresponse) > 0 and 'spec' in jsonresponse.keys():
            sel = Selector(text=jsonresponse['spec'])
            feature_values = dict()

            for f in sel.css('li'):
                f_name = None
                for name in f.css('span *::text').extract():
                    if len(name.strip()) > 0:
                        f_name = name.strip()

                f_values = []
                for v in f.css('div *::text').extract():
                    v = v.strip()
                    if len(v) > 0 and v not in string.punctuation:
                        f_values.append(v)

                if f_name is not None and len(f_values) > 0:
                    self.logger.debug('%s: %s', f_name, ', '.join(f_values))
                    feature_values[f_name] = ', '.join(f_values)

            self.dict_products[product_id]['features'] = feature_values

        # move to next product
        if len(product_without_features) > 0:
            next_product_id = product_without_features.pop()
            self.logger.info(
                'PARSE FEATURES OF product_id=%s', next_product_id)
            yield scrapy.FormRequest(
                url=self.feature_api,
                formdata={'productID': str(next_product_id)},
                callback=self.parse_features,
                meta={'product_id': next_product_id,
                      'product_without_features': product_without_features})

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
        spider = super(TgddProductsSpider, cls).from_crawler(
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
        df = pd.DataFrame.from_dict(self.product_links)
        file_path = 'data/%s_productlinks.csv' % self.category_name
        df.to_csv(file_path, index=False,
                  columns=['product_id', 'product_link'])

        df = pd.DataFrame.from_dict(self.dict_products.values())
        file_path = 'data/%s_products.csv' % self.category_name
        df.to_csv(
            file_path, index=False, encoding='utf-8',
            columns=['product_id', 'top_features', 'features', 'content'])
