# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 21:58:17 2017

@author: Thanh Nguyen
"""
import time
import scrapy
from scrapy import signals
import codecs
from bs4 import BeautifulSoup
import datetime
import calendar
from urllib.parse import urlsplit
import os  
import sys
 
class LinksSpider(scrapy.Spider):
    name="links"
    topic = {}
    def start_requests(self):
        date_from = datetime.datetime(2016, 1, 1, 0, 0, 0)
        date_to = datetime.datetime(2016, 12, 31, 23, 59, 59)
        
        date_from_epoch = calendar.timegm(date_from.timetuple())
        date_to_epoch = calendar.timegm(date_to.timetuple())
        # 1001002: the gioi
        # 1002565: the thao,
        # 1001007: phap luat
        # 1002691: giai tri
        # 1003497: giao duc
        # 1001009: khoa hoc
        # 1001006: oto xe may
        # 1003159: kinh doanh
        # 1002592: so hoa
        # 1002966: gia dinh
        # 1003784: suc khoe
        
        categories = {'the-gioi': 1001002, 'the-thao': 1002565, 'phap-luat': 1001007,
                      'giai-tri': 1002691, 'giao-duc': 1003497, 'khoa-hoc': 1001009,
                      'oto-xe-may': 1001006, 'kinh-doan': 1003159, 
                      'so-hoa': 1002592, 'gia-dinh': 1002966, 'suc-khoe': 1003784}
        pattern = 'http://vnexpress.net/category/day/?cateid=%d&fromdate=%s&todate=%s'
        
        for category_name, category_number in categories.items():
            url = pattern % (category_number, date_from_epoch, date_to_epoch)
            #self.log(url)
            yield scrapy.Request(url=url, callback=self.parse, meta={'category': category_name})
            
    def parse(self, response):
        links  = response.css("ul.list_news  div.title_news a::attr(href)").extract()
        
        category = str(response.meta['category'])            
        filename = 'Links/%s.txt' % category
        with codecs.open(filename, 'a+', "utf-8") as f:
            for link in links:
                f.write('%s\n' % link.strip())
        #self.log('Save file %s' % filename)
    
        NEXT_PAGE_SELECTOR = 'div.pagination_news  a.pa_next::attr(href)'
        next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()
        #self.log(next_page)
        if next_page:
            yield scrapy.Request(
                    url=response.urljoin(next_page),
                    callback=self.parse
                    )

               
class NewsSpider(scrapy.Spider):
    name="news"
    link_directory = "Links"
    crawled_history = "crawled_pages_history.txt"    
    crawled_pages = []
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NewsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    
    def start_requests(self):
        self.load_crawled_pages()
        
        # get all text file in folder Links
        for file in os.listdir(self.link_directory):
            if file.endswith(".txt"):
                file_name = os.path.join(self.link_directory, file)
                #self.log(file_name)
                
                # read all links in each text file
                with open(file_name) as f:
                    links = f.readlines()
                links = [x.strip() for x in links] 
                
                # crawl data for each link
                base = os.path.basename(file_name)
                directory = os.path.splitext(base)[0]
                for link in links:
                    page = link.split("/")[-1]
                    if page not in self.crawled_pages:
                        yield scrapy.Request(url=link, callback=self.parse, meta={'directory': directory})
                        break
                    
            
    def parse(self, response):
        container = response.css("div.main_content_detail")[0]
        title = container.css("div.title_news h1::text").extract_first().strip()
        short_intro = container.css(".short_intro::text").extract_first().strip()       
        paragraphs = container.css("div.fck_detail p.Normal").extract()
        
        self.log(title)
        self.log(short_intro)
        
        content = ''.join(paragraphs).strip()            
        content = BeautifulSoup(content, "lxml").text
        
        if len(content) > 200:
            directory = str(response.meta['directory'])
            
            page = response.url.split("/")[-1]
            filename = '%s/%s.txt' % (directory, page)
            
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filename, 'wb+') as f:
                f.write(title.encode("UTF-8"))
                f.write(short_intro.encode("UTF-8"))
                f.write(content.encode("UTF-8"))
            
            self.log('Save file %s' % filename)
        
            # append history
            self.crawled_pages.append(page)
        
    def spider_closed(self, spider):
        self.log('Spider Closed')
        self.save_crawled_pages()
    
    
    def load_crawled_pages(self):
        if os.path.exists(self.crawled_history):
            with open(self.crawled_history) as f:
                pages = f.readlines()
            self.crawled_pages = [x.strip() for x in pages]
    
    def save_crawled_pages(self):
        with open(self.crawled_history, 'w+') as f:
            for page in self.crawled_pages:
                f.writelines(page + '\n')
        self.log('save history %d' % len(self.crawled_pages))
        