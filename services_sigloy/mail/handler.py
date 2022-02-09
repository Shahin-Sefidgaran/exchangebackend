from fastapi_mail import FastMail, MessageSchema
from fastapi_mail.errors import ConnectionErrors

from logger.loggers import MAIL_LOGGER
from logger.tasks import write_log
from mail.config import mail_configuration

fast_mail = FastMail(mail_configuration)


async def send_mail(message: MessageSchema, template_name: str = None):
    try:
        await fast_mail.send_message(message, template_name=template_name)
    except ConnectionErrors as e:
        write_log(MAIL_LOGGER, 'error', 'mail handler', f'Error in sending mail. Message: {message.dict()}, error:{e}')
