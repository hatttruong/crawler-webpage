from langdetect import detect_langs
import logging


logger = logging.getLogger(__name__)


def is_vietnamese(text):
    """Summary

    Args:
        text (TYPE): Description

    Returns:
        TYPE: Description
    """
    try:
        result = detect_langs(text)
        for r in result:
            if r.lang == 'vi' and r.prob > 0.5:
                return True

        sub_text = text[:500] if len(text) > 500 else text
        logger.info('PROB for text "%s" is %s', sub_text, result)
        return False

    except Exception as e:
        logger.error(e)
        return False
