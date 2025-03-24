import logging
from typing import Any

from rich.logging import RichHandler as Rich


class RichHandler(Rich):
    def __init__(self):
        DATE_FORMAT = '[%d.%m %H:%M:%S]'
        LOGGER_FORMAT = '%(asctime)s %(message)s'

        formatter = logging.Formatter(fmt=LOGGER_FORMAT, datefmt=DATE_FORMAT)

        super().__init__(
            level=logging.DEBUG,
            show_time=False,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_max_frames=10,
        )
        self.setFormatter(formatter)


class Config:
    def __init__(self):
        self.version = 1
        self.disable_existing_loggers = False
        self.handlers = self._get_handlers()
        self.loggers = self._get_loggers()

    def _get_handlers(self):
        handlers: dict[str, Any] = {}

        handlers['console'] = {'class': RichHandler}

        return handlers

    def _get_loggers(self):
        loggers = {
            '': {
                'level': logging.INFO,
                'handlers': list(self.handlers.keys()),
                'propagate': False,
            },
            'uvicorn.error': {
                'level': logging.ERROR,
            },
        }

        return loggers

    def render(self):
        return {
            'version': self.version,
            'disable_existing_loggers': self.disable_existing_loggers,
            'handlers': self.handlers,
            'loggers': self.loggers,
        }


config = Config().render()
