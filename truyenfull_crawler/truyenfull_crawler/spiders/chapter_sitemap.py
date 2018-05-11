# -*- coding: utf-8 -*-
"""Summary
"""
from scrapy.spiders import SitemapSpider
import pandas as pd
from scrapy import signals
from pathlib import Path
import threading


class ChapterSitemapSpider(SitemapSpider):

    """Summary

    Attributes:
        chapters_dict (TYPE): Description
        name (str): Description
        sitemap_follow (list): Description
        sitemap_urls (list): Description
    """
    MAX_CHAPTERS_TO_EXPORT = 100

    name = 'chapter_sitemap'
    sitemap_follow = ['/chapter_sitemap_*']
    sitemap_urls = ['http://truyenfull.vn/sitemap.xml']
    total_crawled = 0
    chapters_dict = dict()

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
        spider = super(ChapterSitemapSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Summary

        Args:
            spider (TYPE): Description
        """
        spider.logger.info('Spider opens: %s', spider.name)
        self.lock = threading.Lock()

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

        content = response.css('div.chapter-c *::text').extract()
        # self.log('content: %s' % content)
        self.chapters_dict[url] = {'url': url, 'content': ' '.join(content)}

        if self.total_crawled % 100 == 0:
            self.log('================= CRAWLED %s PAGES ===============' %
                     self.total_crawled)

        self.lock.acquire()
        try:
            self.total_crawled += 1
            if len(self.chapters_dict) > self.MAX_CHAPTERS_TO_EXPORT:
                self.export()
                self.chapters_dict = dict()
        finally:
            self.lock.release()  # release lock, no matter what

    def export(self):
        """Summary
        """
        self.log('crawled %s pages, export data to csv' %
                 len(self.chapters_dict))
        df = pd.DataFrame.from_dict(list(self.chapters_dict.values()))
        file_path = Path(
            '/data/truyenfull_crawler/chapters_%s.csv' % self.total_crawled)
        df.to_csv(file_path, index=False, columns=['url', 'content'])
