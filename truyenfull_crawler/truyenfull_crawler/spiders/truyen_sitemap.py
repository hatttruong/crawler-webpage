# -*- coding: utf-8 -*-
"""Summary
"""
from scrapy.spiders import SitemapSpider
import pandas as pd
import os
from scrapy import signals


class TruyenSitemapSpider(SitemapSpider):

    """Summary

    Attributes:
        data_dict (TYPE): Description
        name (str): Description
        sitemap_follow (list): Description
        sitemap_urls (list): Description
    """

    name = 'truyen_sitemap'
    sitemap_follow = ['/truyen_sitemap*']
    sitemap_urls = ['http://truyenfull.vn/sitemap.xml']
    data_dict = dict()

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
        spider = super(TruyenSitemapSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """Summary

        Args:
            spider (TYPE): Description
        """
        spider.logger.info('Spider closed: %s', spider.name)
        self.export()

    def parse(self, response):
        """
        Scarpy will automatically extract links in
        "http://truyenfull.vn/sitemap/truyen_sitemap.xml.gz"
        and crawl content of these links. Thus, response are stories' content

        Store url with their categories

        Args:
            response (TYPE): Description
        """
        url = response.request.url
        # self.log('response from url: %s' % url)

        # category
        # '<div class="info"><div>'
        # '<h3>Thể loại:</h3>'
        # '<a itemprop="genre" href="...." title="Ngôn Tình">Ngôn Tình</a>'
        main_cat_nodes = response.css(
            "div.info div a[itemprop*=genre]::text").extract()
        # self.log('main_cat_nodes (before preprocess): %s' % main_cat_nodes)

        main_categories = [c.lower().strip(' ,') for c in main_cat_nodes]
        main_categories = [c for c in main_categories if len(c) > 0]
        # self.log('main_categories (after preprocess): %s' % main_categories)

        # subcategory
        # <div class="desc-text" itemprop="description">
        # <b>Thể loại:</b> Hiện đại<br>
        sub_categories = []
        desc_nodes = response.css("div.desc-text *::text").extract()
        # self.log('desc_nodes: %s' % desc_nodes)
        desc_nodes = [d.lower().strip(' .:') for d in desc_nodes]
        for i in range(len(desc_nodes) - 1):
            if desc_nodes[i] == u'thể loại':
                sub_categories = desc_nodes[i + 1].split(',')
                sub_categories = [s.strip()
                                  for s in sub_categories if len(s.strip()) > 0]
                break
        # self.log('subcategories: %s' % subcategories)
        self.data_dict[url] = {'url': url, 'main_categories': ','.join(
            main_categories), 'sub_categories': ','.join(sub_categories)}

        # if len(self.data_dict) % 100 == 0:
        #     self.export()

    def export(self):
        """Summary
        """
        self.log('crawled %s pages, export data to csv' %
                 len(self.data_dict))
        df = pd.DataFrame.from_dict(list(self.data_dict.values()))
        df.to_csv(
            os.path.join('truyenfull_crawler', 'data', 'truyen_info.csv'),
            index=False,
            columns=['url', 'main_categories', 'sub_categories'])
