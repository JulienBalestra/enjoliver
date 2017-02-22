import logging

from configs import EnjoliverConfig

ec = EnjoliverConfig(importer=__file__)

formatter = logging.Formatter('%(levelname)-7s %(module)-13s %(funcName)s %(message)s')

consoleHandler = logging.StreamHandler()

if ec.logging_level.upper() == "DEBUG":
    consoleHandler.setLevel(logging.DEBUG)
else:
    consoleHandler.setLevel(logging.INFO)

consoleHandler.setFormatter(formatter)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(consoleHandler)
    return logger
