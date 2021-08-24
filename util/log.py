import logging

logger = logging.getLogger(__name__)


def init(path, charset):
    global logger

    logger.setLevel(level=logging.DEBUG)
    handler = logging.FileHandler(filename=path, encoding=charset)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(thread)d - %(funcName)s : %(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
