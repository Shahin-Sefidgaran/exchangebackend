import threading

from logger.tasks import logger_app
from request_queue_handler.consumer import main
from settings import settings

if __name__ == '__main__':
    # requests consumer
    consumer_thread = threading.Thread(target=main)
    consumer_thread.start()

    # logs celery worker
    argv = ['worker',
            '--loglevel=DEBUG',  # THIS OPTION HAS BEEN OVERWRITTEN IN "loggers.py"
            '--concurrency=2',
            ]
    if settings.WRITE_CELERY_LOGS_TO_FILE:
        argv.append('--logfile=logs/celery.log')  # it's writing logs to files instead of stdout

    logger_thread = threading.Thread(target=logger_app.worker_main, args=(argv,))
    logger_thread.start()
