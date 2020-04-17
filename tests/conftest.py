import logging


# mute faker logs
logging.getLogger("faker").setLevel(logging.ERROR)
logging.getLogger("estrade").setLevel(logging.DEBUG)
