import logging

from logger.handlers import TimedRotatingFileCompressorHandler
from settings import settings

# might be written in a better way
_loggers_names = ('network_logger', 'queue_logger',
                  'app_logger', 'db_logger', 'file_logger', 'mail_logger')

NETWORK_LOGGER = _loggers_names[0]
QUEUE_LOGGER = _loggers_names[1]
APP_LOGGER = _loggers_names[2]
DB_LOGGER = _loggers_names[3]
FILES_LOGGER = _loggers_names[4]
MAIL_LOGGER = _loggers_names[5]

formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')


def initiate_celery_logger(logger):
    # setting the root logger level to DEBUG to capture all kind of logs
    logger.setLevel(logging.DEBUG)
    fh = TimedRotatingFileCompressorHandler(filename=f'./logs/celery.log',
                                            when=settings.LOG_ARCHIVE_INTERVAL, encoding='utf-8')
    logger.addHandler(fh)


def initiate_other_loggers():
    for logger_name in _loggers_names:
        file_name = logger_name.replace('_logger', '')
        # archive logs every nights
        fh = TimedRotatingFileCompressorHandler(filename=f'./logs/{file_name}.log',
                                                when=settings.LOG_ARCHIVE_INTERVAL, encoding='utf-8')
        fh.setFormatter(formatter)
        fh.setLevel(logging.NOTSET)
        logger = logging.getLogger(logger_name)
        logger.addHandler(fh)
