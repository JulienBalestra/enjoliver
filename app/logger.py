import logging
from configs import EnjoliverConfig

formatter = logging.Formatter('%(asctime)-8s %(levelname)-5s %(module)-4s %(message)s')

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
