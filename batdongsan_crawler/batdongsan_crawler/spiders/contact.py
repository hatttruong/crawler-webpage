import scrapy


class ContactItem(scrapy.Item):
    name = scrapy.Field()
    join_date = scrapy.Field()
    address = scrapy.Field()
    email = scrapy.Field()
