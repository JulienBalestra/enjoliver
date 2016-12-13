import logging

formatter = logging.Formatter('%(asctime)-8s %(levelname)-5s %(module)-4s %(message)s')

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(consoleHandler)
    return logger

