"""Summary

Attributes:
    logger (TYPE): Description
"""
import dateutil.parser
import logging


logger = logging.getLogger(__name__)


class BaseFbObject():

    """Summary

    Attributes:
        id (TYPE): Description
        url (TYPE): Description
    """

    def __init__(self, id):
        """Summary

        Args:
            id (TYPE): Description

        """
        self.id = id


class FbUser(BaseFbObject):

    """Summary
    """

    def __init__(self, url, id):
        """Summary

        Args:
            url (TYPE): Description
            id (TYPE): Description
        """
        super(FbUser, self).__init__(url, id)


class FbGroup(BaseFbObject):

    """Summary
    """

    def __init__(self, id):
        """Summary

        Args:
            id (TYPE): Description

        """
        super(FbGroup, self).__init__(id)


class FbPage(BaseFbObject):

    """Summary
    """

    def __init__(self, page_id, name, liked_pages=None):
        """Summary

        Args:
            page_id (TYPE): Description
            name (TYPE): Description
            liked_pages (None, optional): Description
        """
        self.page_id = page_id
        self.username = name
        self.name = ''
        self.liked_pages = set()
        self.about = ''
        self.description = ''
        self.company_overview = ''
        self.mission = ''
        self.talking_about_count = 0
        self.fan_count = 0
        self.last_active = None
        if liked_pages is not None:
            self.liked_pages = set(liked_pages)

    def add_liked_page(self, liked_page_id):
        """Summary

        Args:
            liked_page_id (TYPE): Description
        """
        self.liked_pages.add(liked_page_id)

    def to_dict(self):
        """
        reuse __dict__ property, modify value of created_time & crawled_utctime

        Returns:
            TYPE: Description
        """
        dict_obj = dict(self.__dict__)
        dict_obj['liked_pages'] = ','.join(self.liked_pages)
        return dict_obj


class FbPost():

    """Summary

    Attributes:
        angry (TYPE): Description
        crawled_utctime (TYPE): Description
        created_time (TYPE): Description
        haha (TYPE): Description
        id (TYPE): Description
        like (TYPE): Description
        love (TYPE): Description
        message (TYPE): Description
        owner_id (TYPE): Description
        sad (TYPE): Description
        type (TYPE): Description
    """

    def __init__(self, owner_id, data_json):
        """
        Args:
            owner_id (TYPE): Description
            data_json (TYPE): Description

        Deleted Parameters:
            url (TYPE): Description
            id (TYPE): Description
        """
        self.owner_id = owner_id
        self.id = data_json['id']
        self.message = data_json['message']
        self.created_time = dateutil.parser.parse(
            data_json['created_time'])
        self.type = data_json['type']
        self.like = data_json['like']['summary']['total_count']
        self.love = data_json['love']['summary']['total_count']
        self.haha = data_json['haha']['summary']['total_count']
        self.sad = data_json['sad']['summary']['total_count']
        self.angry = data_json['angry']['summary']['total_count']
        self.crawled_utctime = data_json['crawled_utctime']

    def to_dict(self):
        """
        reuse __dict__ property, modify value of created_time & crawled_utctime

        Returns:
            TYPE: Description
        """
        dict_obj = dict(self.__dict__)
        # dict_obj['created_time'] = self.created_time.strftime(
        #     constant.STR_DATETIME_FORMAT)
        # dict_obj['crawled_utctime'] = self.crawled_utctime.strftime(
        #     constant.STR_DATETIME_FORMAT)
        return dict_obj
