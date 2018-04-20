# -*- coding: utf-8 -*-
"""Summary
"""
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
from scrapy.exceptions import CloseSpider
from listing import ListingItem
from contact import ContactItem


class MuabannetSpider(CrawlSpider):

    """Summary

    Attributes:
        allowed_domains (list): Description
        contacts (list): Description
        custom_settings (TYPE): Description
        listings (list): Description
        name (str): Description
        rules (TYPE): Description
        start_urls (list): Description
        urls (list): Description
    """

    name = 'muabannet'
    allowed_domains = ['muaban.net']
    start_urls = ['http://muaban.net/']
    custom_settings = {
        'LOG_FILE': 'scrapy_muaban.log',
    }

    urls = []
    listings = []
    contacts = []

    rules = (
        # root link from which we extract all other links
        Rule(LinkExtractor(
            'https://muaban.net/mua-ban-nha-dat-cho-thue-toan-quoc-l0-c3')),

        # links which contain data
        Rule(LinkExtractor(
            allow=r'https://muaban\.net/(\w|\-){10,}/(\w|\-){10,}id\d{3,}'),
            callback='parse_item',
            follow=True),
    )

    def validate_response(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Returns:
            TYPE: Description
        """
        return True

    def parse_item(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Returns:
            TYPE: Description
        """
        # validate response if it belongs to real estate or not
        if self.validate_response(response) is False:
            return

        # add url to container
        print('Extracting page: %s' % response.url)
        self.urls.append(response.url)
        print('total urls: %d' % len(self.urls))

        listingLoader = ItemLoader(item=ListingItem(), response=response)
        listingLoader.add_value('source_url', response.url)
        # l.add_xpath('name', xpath1) # (1)
        # l.add_xpath('name', xpath2) # (2)
        # l.add_css('name', css) # (3)
        # l.add_value('name', 'test') # (4)
        self.listings.append(listingLoader.load_item())
        print('total listings: %d' % len(self.listings))

        contactLoader = ItemLoader(item=ContactItem(), response=response)
        # contactLoader.add_value('source_url', response.url)
        self.contacts.append(contactLoader.load_item())
        print('total contacts: %d' % len(self.contacts))

        if len(self.urls) == 1:
            raise CloseSpider('number of urls exceeded')

    def export_data(self):
        """Export crawled data to file
        """
        # export crawled urls
        # export contacts
        # export listings
