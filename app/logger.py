"""
Construct a logger for the application
"""
import logging

import configs
# from configs import EnjoliverConfig

EC = configs.EnjoliverConfig(importer=__file__)

FORMATTER = logging.Formatter('%(levelname)-7s %(module)-8s %(funcName)s %(message)s')

CONSOLE_HANDLER = logging.StreamHandler()

if EC.logging_level.upper() == "DEBUG":
    CONSOLE_HANDLER.setLevel(logging.DEBUG)
else:
    CONSOLE_HANDLER.setLevel(logging.INFO)

CONSOLE_HANDLER.setFormatter(FORMATTER)


def get_logger(name):
    """
    Get the generated logger for the application
    :param name: usually the name of the __file__
    :return:
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(CONSOLE_HANDLER)
    return logger
