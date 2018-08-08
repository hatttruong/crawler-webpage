"""
Tiki categories:
'https://tiki.vn/dien-thoai-may-tinh-bang/c1789'
'https://tiki.vn/phu-kien-dien-thoai/c8214'

Dienmayxanh
https://www.dienmayxanh.com/dien-thoai
https://www.dienmayxanh.com/phu-kien

Thegioididong
https://www.thegioididong.com/aj/CategoryV5/Product
42 dienthoaididong
https://www.thegioididong.com/aj/AccessoryV4/HomeProduct
https://www.thegioididong.com/aj/AccessoryV4/Product

lazada
https://www.lazada.vn/dien-thoai-di-dong/
https://www.lazada.vn/phu-kien-dien-thoai-may-tinh-bang/?location=South,Ho%20Chi%20Minh,North,Hanoi

vienthonga
https://vienthonga.vn/Category/LoadMoreCate?cateid=152535&page=%s
https://vienthonga.vn/linh-phu-kien-dien-thoai

"""
TIKI_CATEGORY = 'tiki_phu-kien-dien-thoai'
TIKI_CAT_URL = 'https://tiki.vn/phu-kien-dien-thoai/c8214'

DMX_CATEGORY = 'dmx_dien-thoai'
DMX_CAT_URL = 'https://www.dienmayxanh.com/dien-thoai'

TGDD_DTDD = {
    'rating_api': 'https://www.thegioididong.com/aj/ProductV4/RatingCommentList/',
    'feature_api': 'https://www.thegioididong.com/aj/ProductV4/GetFullSpec/',
    'dtdd': {
        'name': 'tgdd_dtdd',
        'api': 'https://www.thegioididong.com/aj/CategoryV5/Product',
        'params': {
            'Category': '42',
            'PageSize': '30',
            'PageIndex': '0'
        },
    },
    'tainghe': {
        'name': 'tgdd_tainghe',
        'api': 'https://www.thegioididong.com/aj/AccessoryV4/Product',
        'params': {
            'Category': '54',
            'Size': '20',
            'Index': '0'
        },
    },
    'pin_sac':
    {
        'name': 'tgdd_pin_sac',
        'api': 'https://www.thegioididong.com/aj/AccessoryV4/Product',
        'params': {
            'Category': '57',
            'Size': '20',
            'Index': '0'
        },
    },
    'cap_sac':
    {
        'name': 'tgdd_cap_sac',
        'api': 'https://www.thegioididong.com/aj/AccessoryV4/Product',
        'params': {
            'Category': '58',
            'Size': '20',
            'Index': '0'
        },
    },
    'chuot':
    {
        'name': 'tgdd_chuot',
        'api': 'https://www.thegioididong.com/aj/AccessoryV4/Product',
        'params': {
            'Category': '86',
            'Size': '20',
            'Index': '0'
        },
    },
    'loa':
    {
        'name': 'tgdd_loa',
        'api': 'https://www.thegioididong.com/aj/AccessoryV4/Product',
        'params': {
            'Category': '382',
            'Size': '20',
            'Index': '0'
        },
    },

}


LAZADA_CATEGORY = {
    'review_api': 'https://my.lazada.vn/pdp/review/getReviewList?itemId=%s&pageSize=5&filter=0&sort=0&pageNo=%s',
    'dtdd': {
        'name': 'lazada_dien-thoai-di-dong',
        'url': 'https://www.lazada.vn/dien-thoai-di-dong/?page=',
    },
    'phu_kien': {
        'name': 'lazada_phu_kien',
        'url': 'https://www.lazada.vn/phu-kien-dien-thoai-may-tinh-bang/?page='
    }
}

VTA_CATEGORY = {
    'dtdd': {
        'name': 'vta_dien-thoai-smartphones',
        'url': 'https://vienthonga.vn/Category/LoadMoreCate?cateid=152535&page=%s'
    },
    'phu_kien': {
        'name': 'vta_phu_kien',
        'url': 'https://vienthonga.vn/linh-phu-kien-dien-thoai'
    }
}

VTA_XML_NAMESPACE = 'http://schemas.datacontract.org/2004/07/WebApiPublic_V2.Models'
