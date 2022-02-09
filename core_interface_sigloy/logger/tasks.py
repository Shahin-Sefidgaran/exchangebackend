import logging

from celery.signals import after_setup_task_logger
from celery.utils.log import get_task_logger

from logger.loggers import initiate_other_loggers, initiate_celery_logger
from msg_brokers.celery.engine import logger_app
from settings import settings


@after_setup_task_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """initiate all loggers write logs from the application"""
    initiate_celery_logger(logger)
    initiate_other_loggers()


@logger_app.task
def create_log_task(logger: str, level: str, author: str, msg: str):
    logger = get_task_logger(logger)
    return logger.log(logging.getLevelName(level.upper()), author + ': ' + msg)


def write_log(logger: str, level: str, author: str, msg: str):
    """ Send a log message using celery to be consumed by the worker and
        to be written to the disk file"""
    if settings.ENABLE_LOGGING:
        create_log_task.delay(logger, level, author, msg)
