import logging


def setup():
    # set up logging in general
    FORMAT = "%(name)s [%(levelname)s] %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    # set up logger
    logger = logging.getLogger("appimagecraft.main")
    logger.setLevel(logging.INFO)

    # logger.addHandler(logging.han)


def get_logger(context: str = ""):
    logger_prefix = "appimagecraft"

    logger_name = logger_prefix

    if context:
        logger_name += "." + str(context)

    return logging.getLogger(logger_name)
