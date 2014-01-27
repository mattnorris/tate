#! /usr/local/bin/python
# Title:        tate.py
# Description:  Processes Tumblr Likes and Posts by using Yahoo Pipes,
#               extracting each post's details from JSON and emailing them
#               to Evernote.
# Author:       Matthew Norris
# References:   http://pipes.yahoo.com/wraithmonster/tumblrlikes
#               http://pipes.yahoo.com/wraithmonster/tumblrposts
#               http://codecomments.wordpress.com/2008/01/04/python-gmail-smtp-example/

################################################################################
# Imports
################################################################################
import json
import glob

import os
import smtplib
import mimetypes

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.encoders import encode_base64

import tempfile
import time

import urllib2

################################################################################
# Constants
################################################################################

# TODO: Move out of this file and into a config file.
USER = 'GMAIL_ADDRESS'
PASSWORD = 'GMAIL_PASSWORD'
RECIPIENT = 'EVERNOTE_EMAIL_ADDRESS'

TUMBLR_USER = "TUMBLR_USERNAME"
LIKES_URL = "http://pipes.yahoo.com/pipes/pipe.run?_id=d899c240db65460307e5a977a300e841&_render=json&items-count=50"
POSTS_URL = "http://pipes.yahoo.com/pipes/pipe.run?_id=85a512643cd18305864601ac03d5269b&_render=json&intPosts=50&startPost=%d&strUser=%s"

################################################################################
# Feed Reader  
################################################################################

# http://stackoverflow.com/a/925630/154065
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def removeNonAscii(s):
    """
    Removes non-ASCII characers from the given string and returns the result.
    Based on http://stackoverflow.com/questions/1342000
    """
    return "".join(filter(lambda x: ord(x)<128, s))

def mktmpdir(dir_root):
    """
    Creates a temporary directory based on the current time,
    prefixed with the title "tumblr".
    """
    timestr = str(int(time.time()))
    # http://docs.python.org/library/tempfile.html
    return tempfile.mkdtemp(prefix='tumblr_%s_' % timestr, dir=dir_root)

def processPhoto(photo_url, dir, dryrun=False):
    """
    Saves a local copy of the photo at the given URL and returns the local
    path to it.
    """
    if not dir and not dryrun:
        dir = mktmpdir(os.getcwd())

    local_path = os.path.join(dir, os.path.basename(photo_url))
    if not dryrun:
        photo = urllib2.urlopen(photo_url)
        local_file = open(local_path, 'wb')
        local_file.write(photo.read())
        local_file.close()
    else:
        print 'Photo would be saved to %s' % local_path

    return local_path

def getPosts(rmtmp=False, dryrun=False):
    """
    Only gets photo posts for now. Only searches a docs directory for .json files.

    Evernote has a:
        Link URL
        Description
        Notebook
        Tags

    You can send notes into specific notebooks and assign tags by adding some
    simple information into the subject of the email. Here's how:

    Notebook: Add @[notebook name] to the end of the subject line.
    Tag: Add #[tag name] at the end of the subject line. This feature works with existing tags in your account.
    Be sure to follow this order: subject, notebook name, tags.

    Example subject line:
        Fwd: Recipe for Bouillabaisse @Recipes #soup #fish #french
    """
    # Create a temporary folder for processing the photos.
    dir_root = os.path.join(os.getcwd(), '../tmp')
    dir = mktmpdir(dir_root)

    # http://bogdan.org.ua/2007/08/12/python-iterate-and-read-all-files-in-a-directory-folder.html
    # TODO: Add ability to specify a folder of JSON files.
    path = os.path.join(os.getcwd(), '../docs')
    for infile in glob.glob(os.path.join(path, 'tumblr*.json')):
        print "Processing", infile
        # http://docs.python.org/tutorial/inputoutput.html#reading-and-writing-files
        f = open(infile)
        # http://docs.python.org/library/json.html#module-json
        posts = json.loads(f.read())['value']['items']
        f.close()

        print "Iterating through %d posts now..." % len(posts)
        # http://stackoverflow.com/questions/1185545/python-loop-counter-in-a-for-loop
        for counter, post in enumerate(posts):
            type = post['type']
            if type == 'photo':
                print "Post %d is a photo." % counter
                link_url = post['link']
                # http://docs.python.org/tutorial/errors.html
                try:
                    tags = post['tag']
                except KeyError:
                    print "No tags for post %d." % counter

                descr = ''
                try:
                    descr = unicode(strip_tags(post['photo-caption']))
                except KeyError:
                    print "No caption for post %d." % counter

                # http://docs.python.org/release/2.5.2/lib/string-methods.html
                title = post['slug'].replace('-', ' ') or descr[:30] or type

                # Create a list to store the processed photos.
                attachments = []

                # Get the first photo (guaranteed to be there).
                photo_1 = post['photo-url'][0]
                attachments.append(processPhoto(photo_1['content'],
                    dir, dryrun=dryrun))

                # Get other photos (not guaranteed to be there).
                try:
                    # Don't process the first photo in the set;
                    # it's a duplicate of photo_1.
                    photos = post['photoset']['photo'][1:]

                    for p_count, photo in enumerate(photos):
                        print 'Processing photo %d.' % p_count
                        photo_n = photo['photo-url'][0]
                        attachments.append(processPhoto(photo_n['content'],
                            dir, dryrun=dryrun))
                except KeyError:
                    print 'No photoset for post %d.' % counter

                # Send the gathered photos in an email to Evernote.
                print 'Preparing an email to Evernote...'

                subject = '%s %s #tumblr #src:script' % (title,
                                     ' '.join(['#%s' % tag for tag in tags]))
                body_tags = ', '.join([tag for tag in tags]) + \
                            ', tumblr, src:script'
                body = '%s\n\n%s\n\n*NOTE*: Some tags may not have worked ' \
                'because Evernote needs incoming tags from email to exist ' \
                'before they can be saved. If this is the case, copy/paste ' \
                'the tags below:\n\n%s\n\n' % \
                       (link_url, descr, body_tags.lower())

                # Encode the email contents.
                # http://docs.python.org/howto/unicode.html
                subject = subject.encode('utf-8', 'ignore')
                body = body.encode('utf-8', 'ignore')

                if dryrun:
                    print '>>>>> Subject:', subject.lower()
                    print '>>>>> Body:', body
                    print '>>>>> Attaching %d photos: %s' % (len(attachments), attachments)

                print 'Sending email with %d attachments...' % len(attachments)
                if not dryrun:
                    sendMail(subject.lower(), body, *attachments)
                print 'Done.'
                print '------------------------------------------------------\n'

    # Delete the temporary folder created.
    if rmtmp:
        os.rmdir(dir)

################################################################################
# Email
################################################################################

def sendMail(subject, text, *attachmentFilePaths):
    """
    Sends an email with the specified subject, body, and attachments.
    """
    gmailUser = USER
    gmailPassword = PASSWORD
    recipient = RECIPIENT

    msg = MIMEMultipart()
    msg['From'] = gmailUser
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for attachmentFilePath in attachmentFilePaths:
        msg.attach(getAttachment(attachmentFilePath))

    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmailUser, gmailPassword)
    mailServer.sendmail(gmailUser, recipient, msg.as_string())
    mailServer.close()

    print('Sent email to %s' % recipient)


def getAttachment(attachmentFilePath):
    """
    Formats the file on the given path and assigns the proper MIME type.
    """
    contentType, encoding = mimetypes.guess_type(attachmentFilePath)

    if contentType is None or encoding is not None:
        contentType = 'application/octet-stream'
    mainType, subType = contentType.split('/', 1)
    file = open(attachmentFilePath, 'rb')

    if mainType == 'text':
        attachment = MIMEText(file.read())
    elif mainType == 'message':
        attachment = email.message_from_file(file)
    elif mainType == 'image':
        attachment = MIMEImage(file.read(), _subType=subType)
    elif mainType == 'audio':
        attachment = MIMEAudio(file.read(), _subType=subType)
    else:
        attachment = MIMEBase(mainType, subType)
        attachment.set_payload(file.read())
        encode_base64(attachment)

    file.close()
    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachmentFilePath))
    return attachment

def test_tumblr_read():
    """
    Reads Tumblr posts directly from Yahoo Pipes, not a file.
    """
    # TODO: Add processing for reading JSON from Yahoo Pipes.
    print '{}'

def test_email():
    """
    Sends a test email.
    """
    files = []
    files.append(os.path.join(os.getcwd(), '../test/input', 'yahoo-email.py.txt'))
    files.append(os.path.join(os.getcwd(), '../test/input', 'yahoo-email.py'))
    files.append(os.path.join(os.getcwd(), '../test/input', 'evernote-logo.jpg'))

    sendMail("Testing", 'this is the body', *files)

if __name__ == "__main__":
    getPosts(dryrun=False)