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


# Example usage:
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = CustomFormatter("%(log_color)s%(levelname)s%(reset)s: %(message_padding)s%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
