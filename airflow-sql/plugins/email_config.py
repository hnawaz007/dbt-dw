from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.message import EmailMessage
from email import encoders
import smtplib
import os
import json
import io


#
email = "hnawaz@localmail.com"
password = "aneela01"
sender = 'admin@localmail.com'

def send_mail(to, subject, body):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = 'admin@localmail.com'
    message['To'] = to

    body_content = body
    message.attach(MIMEText(body_content, "html"))
    msg_body = message.as_string()

    server = smtplib.SMTP('192.168.1.39')
    server.login(email, password)
    server.sendmail(sender, to, msg_body)
    #
    server.quit()