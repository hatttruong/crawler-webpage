# -*- coding: utf-8 -*-
import scrapy


class BatdongsanSpider(scrapy.Spider):
    name = 'batdongsan'
    allowed_domains = ['batdongsan.com.vn']
    start_urls = ['http://batdongsan.com.vn/']

    def parse(self, response):
        pass
