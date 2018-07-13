from flask_mail import Mail, Message
from flask import render_template
from . import mail


def send_email(to, title, template, **kwargs):
    msg = Message(title, sender='739144313@qq.com', recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    # msg.html = render_template(template + '.html', **kwargs)
    print('111')
    mail.send(msg)
    print('邮件发送完成')