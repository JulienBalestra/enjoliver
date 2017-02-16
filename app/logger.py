import logging
from configs import EnjoliverConfig

formatter = logging.Formatter('\r%(levelname)-7s %(module)-13s %(funcName)s %(message)s')

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)

ec = EnjoliverConfig()


def get_logger(name):
    logger = logging.getLogger(name)
    if ec.logging_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(consoleHandler)
    return logger
