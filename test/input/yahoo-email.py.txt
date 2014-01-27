#! /usr/local/bin/python

SMTPserver = 'smtp.att.yahoo.com'
sender =     'me@my_email_domain.net'
destination = ['recipient@her_email_domain.com']

USERNAME = "USER_NAME_FOR_INTERNET_SERVICE_PROVIDER"
PASSWORD = "PASSWORD_INTERNET_SERVICE_PROVIDER"

# typical values for text_subtype are plain, html, xml
text_subtype = 'plain'

content="""\
Test message
"""

subject="Sent from Python"

import sys
import os
import re

from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
from email.mime.text import MIMEText

try:
    msg = MIMEText(content, text_subtype)
    msg.subject = subject
    msg.sender = sender

#    msg['Subject']=       subject
#    msg['From']   = sender # some SMTP servers will do this automatically, not all

    conn = SMTP(SMTPserver)
    conn.set_debuglevel(False)
    conn.login(USERNAME, PASSWORD)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.close()

except Exception, exc:
    sys.exit( "mail failed; %s" % str(exc) ) # give a error message