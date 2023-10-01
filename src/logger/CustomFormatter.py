import logging


class CustomFormatter(logging.Formatter):
    """ """

    def __init__(self, fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt='<%m/%d/%Y %H:%M:%S>'):
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)

    def format(self, record):

        # Remember the original format
        format_orig = self._style._fmt

        if record.levelno == logging.ERROR:
            self._style._fmt = "%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s"

        # Calling the original formatter once the style has changed
        result = logging.Formatter.format(self, record)

        # Restore the original format
        self._style._fmt = format_orig

        return result