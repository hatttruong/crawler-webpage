import scrapy


class ListingItem(scrapy.Item):
    category = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    created_date = scrapy.Field()
    expired_date = scrapy.Field()
    address = scrapy.Field()
    area = scrapy.Field()
    width = scrapy.Field()
    length = scrapy.Field()

    price = scrapy.Field()
    floor = scrapy.Field()
    bedrooms = scrapy.Field()
    bathrooms = scrapy.Field()
    width_street = scrapy.Field()
    keywords = scrapy.Field()
    # source of listing such as batdongsan, chotot...
    source_url = scrapy.Field()
    original_id = scrapy.Field()
