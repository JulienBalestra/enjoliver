import logging

from configs import EnjoliverConfig

ec = EnjoliverConfig()


def get_logger(name):
    formatter = logging.Formatter('%(levelname)-7s %(module)-13s %(funcName)s %(message)s')
    logger = logging.getLogger(name)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    if ec.logging_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)
    return logger
