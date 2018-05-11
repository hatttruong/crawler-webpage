# -*- coding: utf-8 -*-
"""
Attributes:
    logger (TYPE): Description
"""
import scrapy
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class Icd9Spider(scrapy.Spider):

    """Summary

    Attributes:
        icd_codes_dict (TYPE): Description
        name (str): Description

    Deleted Attributes:
        topic (dict): Description
    """

    name = "icd9"
    icd_codes_dict = dict()

    def start_requests(self):
        """Summary

        Yields:
            TYPE: Description
        """
        url = 'http://www.icd9data.com/2015/Volume1/default.htm'
        yield scrapy.Request(url=url, callback=self.parse,
                             meta={'level': 1, 'parent': -1})

    def parse(self, response):
        """Summary

        Args:
            response (TYPE): Description

        Yields:
            TYPE: Description
        """
        move_next_level = True
        level = int(response.meta['level'])
        parent = str(response.meta['parent'])
        self.log('parse level=%s, parent=%s' % (level, parent))

        icd_codes = response.css("div.definitionList ul li")
        icd_descs = response.css("div.definitionList ul li::text").extract()
        icd_descs = [i.strip() for i in icd_descs if len(i.strip()) > 0]
        if len(icd_codes) == 0:
            icd_codes = response.css("ul.definitionList li")
            icd_descs = response.css("ul.definitionList li::text").extract()
            icd_descs = [i.strip() for i in icd_descs if len(i.strip()) > 0]
            if len(icd_codes) == 0:
                icd_codes = response.css("span.localLine")
                icd_descs = response.css(
                    "span.localLine span.threeDigitCodeListDescription::text"
                ).extract()
                icd_descs = [i.strip()
                             for i in icd_descs if len(i.strip()) > 0]
                move_next_level = False
                if len(icd_codes) == 0:
                    self.log(
                        'level=%s, url=%s, HAVE NO ICD CODE with span.localLine' %
                        (level, response.request.url))

        for (icd_code, desc) in zip(icd_codes, icd_descs):
            # get icd-code, title, link
            code = icd_code.css("a.identifier::text").extract_first()
            link = icd_code.css("a.identifier::attr(href)").extract_first()
            self.log('Icd_code=%s, link=%s, description=%s' %
                     (code, link, desc))
            if code in self.icd_codes_dict.keys():
                continue

            self.icd_codes_dict[code] = {'code': code, 'link': link,
                                         'desc': desc, 'level': level,
                                         'parent': parent}

            if move_next_level:
                self.log('crawled=%s, follow link=%s, level=%s, parent=%s' %
                         (len(self.icd_codes_dict), link, level + 1, code))
                yield scrapy.Request(
                    url=response.urljoin(link),
                    callback=self.parse,
                    meta={'level': level + 1, 'parent': code}
                )

        if len(icd_codes) == 0 or move_next_level is False:
            self.export()
            self.log('DONE for this code=%s' % parent)

    def export(self):
        """
        Export all icd code to csv
        """
        self.log('export data to csv')
        df = pd.DataFrame.from_dict(
            [item for code, item in self.icd_codes_dict.items()])
        df.to_csv('icd9_data.csv', index=False,
                  columns=['parent', 'code', 'desc', 'level'])
