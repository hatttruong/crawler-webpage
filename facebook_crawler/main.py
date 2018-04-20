"""Summary
"""
import page_helper
import logging


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

if __name__ == '__main__':
    BASE_DIR = '..'
    # test_page(page_name='nhatkyyeunuoc1')
    # get_current_posts(page_name='nhatkyyeunuoc1',
    #                   output_path=os.path.join(BASE_DIR, 'data', 'content'))
    # get_history_posts(page_name='nhatkyyeunuoc1',
    #                   output_path=os.path.join(BASE_DIR, 'data', 'content'),
    #                   year_from=2015,
    #                   year_to=2018)

    page_helper.get_liked_pages_by()
