# -*- coding: utf-8 -*-
"""
Contains pipelines as follow:
    1. BatdongsanCrawlerPipeline: do nothing
    2. DuplicatesPipeline: check if url is crawled or not
    3. ScreenshotPipeline: save a screen shot with the response of url
"""

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import scrapy
import hashlib
try:
    from urllib.parse import quote
except ImportError:
    from urllib import pathname2url as quote


class BatdongsanCrawlerPipeline(object):

    """Summary
    """

    def process_item(self, item, spider):
        """Summary

        Args:
            item (TYPE): Description
            spider (TYPE): Description

        Returns:
            TYPE: Description
        """
        print('BatdongsanCrawlerPipeline')
        return item


class DuplicatesPipeline(object):

    """Store seen url when crawling

    Attributes:
        urls_seen (TYPE): set of crawled urls

    """

    def __init__(self):
        """Summary
        """
        self.urls_seen = set()

    def process_item(self, item, spider):
        """Summary

        Args:
            item (TYPE): Description
            spider (TYPE): Description

        Returns:
            TYPE: Description

        Raises:
            DropItem: Description
        """
        print('DuplicatesPipeline')
        print('source_url: %s' % item['source_url'])
        url_hash = hashlib.md5(item['source_url'].encode('utf8')).hexdigest()
        if url_hash in self.urls_seen:
            raise DropItem('Duplicate item found: %s' % item)
        else:
            self.urls_seen.add(url_hash)
            return item


class ScreenshotPipeline(object):
    """Pipeline that uses Splash to render screenshot of
    every Scrapy item.

    Attributes:
        SPLASH_URL (TYPE): Description
    """

    SPLASH_URL = 'http://localhost:8050/render.png?url={}'

    def process_item(self, item, spider):
        """Summary

        Args:
            item (TYPE): Description
            spider (TYPE): Description

        Returns:
            TYPE: Description
        """
        print('ScreenshotPipeline: process_item')
        encoded_item_url = quote(item['url'])
        screenshot_url = self.SPLASH_URL.format(encoded_item_url)
        request = scrapy.Request(screenshot_url)
        dfd = spider.crawler.engine.download(request, spider)
        dfd.addBoth(self.return_item, item)
        return dfd

    def return_item(self, response, item):
        """Summary

        Args:
            response (TYPE): Description
            item (TYPE): Description

        Returns:
            TYPE: Description
        """
        print('ScreenshotPipeline: return_item')

        if response.status != 200:
            # Error happened, return item.
            return item

        # Save screenshot to file, filename will be hash of url.
        url = item['url']
        url_hash = hashlib.md5(url.encode('utf8')).hexdigest()
        filename = '{}.png'.format(url_hash)
        with open(filename, 'wb') as f:
            f.write(response.body)

        # Store filename in item.
        item['screenshot_filename'] = filename
        return item
