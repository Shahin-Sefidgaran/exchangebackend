from datetime import datetime

import aiohttp
from aiohttp import ClientError
from fastapi import Request
from user_agents import parse

from authentication import crud, models
from db.pgsql.engine import AsyncDBSession
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from mail.handler import send_mail
from mail.shared import MailMessage


async def delete_unused_verification(verification: models.Verification):
    """Delete the verification record from database.
    This task is used when we are using "DB" as "TWO_FA_CODES_STORAGE"."""
    async with AsyncDBSession() as async_session:
        await crud.delete_verification(async_session, verification)


async def new_login_happened(request: Request, user: models.User):
    agent = request.headers['user-agent']
    parsed_agent = str(parse(agent))
    ip = request.client.host
    if ip == '127.0.0.1':
        response = {'city': 'home', 'region': 'home', 'country': 'home'}
    else:
        try:
            ip_info_url = 'https://ipinfo.io/' + ip + '/json'
            async with aiohttp.ClientSession() as session:
                async with session.get(ip_info_url) as resp:
                    response = await resp.json()
        except ClientError as e:
            write_log(APP_LOGGER, 'warning', 'login history saver',
                      f"couldn't find location of {ip}, reason: {e}")
            response = {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}

    # Save user login
    city = response['city']
    region = response['region']
    country = response['country']
    async with AsyncDBSession() as async_session:
        await crud.create_new_login_history(async_session, user, parsed_agent, ip, agent, city, region, country)

    # Send Mail Notification
    now = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
    text = f"""<p>New login is happened on: {now}</p>
<p>Ip: {ip}</p>
<p>Location: {country} {region} {city}</p>
"""
    msg = MailMessage(subject="New Login",
                      recipients=[user.email],
                      template_body={"message": text},
                      subtype="html")
    await send_mail(msg, 'new_activity.jinja2')


async def notify_password_changed(user: models.User):
    now = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
    msg = MailMessage(subject="Password Changed",
                      recipients=[user.email],
                      template_body={"message": f"Your password changed on: {now}"},
                      subtype="html")
    await send_mail(msg, 'new_activity.jinja2')
