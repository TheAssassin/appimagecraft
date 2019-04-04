import coloredlogs
import logging


def setup(loglevel=logging.INFO, with_timestamps=False):
    fmt = "%(name)s[%(process)s] [%(levelname)s] %(message)s"

    if with_timestamps:
        fmt = "%(asctime)s " + fmt

    if loglevel <= logging.DEBUG:
        fmt = "%(pathname)s:%(lineno)d:\n" + fmt

    # basic logging setup
    styles = coloredlogs.DEFAULT_FIELD_STYLES
    styles["pathname"] = {
        "color": "magenta",
    }
    styles["levelname"] = {
        "color": "cyan",
    }
    coloredlogs.install("DEBUG", fmt=fmt, styles=styles)

    # set up logger
    logger = logging.getLogger("appimagecraft.main")
    logger.setLevel(loglevel)

    # logger.addHandler(logging.han)


def get_logger(context: str = ""):
    logger_prefix = "appimagecraft"

    logger_name = logger_prefix

    if context:
        logger_name += "." + str(context)

    return logging.getLogger(logger_name)
