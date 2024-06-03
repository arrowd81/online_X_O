import logging


class CustomFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[34m',  # Blue
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        levelname = record.levelname
        message = record.getMessage()
        message_padding = ' ' * (10 - len(levelname) - 2)  # Calculate padding based on level name length
        log_color = self.COLORS.get(levelname, self.COLORS['RESET'])
        record.log_color = log_color
        record.reset = self.COLORS['RESET']
        record.message_padding = message_padding
        return super().format(record)


logger = logging.getLogger()
formatter = CustomFormatter("%(log_color)s%(levelname)s%(reset)s: %(message_padding)s%(message)s")
# console output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# file output
file_handler = logging.FileHandler('online_X_O.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# level
logger.setLevel(logging.INFO)
