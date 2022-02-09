# import asyncio
#
# from mail.handler import send_mail
# from mail.shared import MailMessage
#
#
# async def main():
#     msg = MailMessage(subject="The new subject of the mail",
#                       recipients=['aligh1afm@gmail.com'],  # List of recipients, as many as you can pass
#                       # body='This is a test email',
#                       template_body={"variable": 'kasdfks'},
#                       subtype="html")
#     await send_mail(msg, 'register_verify.jinja2')
#
#
# asyncio.run(main())
