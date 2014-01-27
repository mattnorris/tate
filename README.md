# TATE
## Tumblr Archive To Evernote

IFTTT has made it very easy to send your Tumblr posts into Evernote (or most anywhere else, for that matter), but if you haven't set it up yet, odds are you have a ton of posts you would like to export. TATE does just that. 

# Get Started 

## Clone

Clone this repository. 

    git clone https://github.com/mattnorris/tate.git

Clone these Yahoo Pipes: 
- http://pipes.yahoo.com/wraithmonster/tumblrlikes
- http://pipes.yahoo.com/wraithmonster/tumblrposts

## Save

Run the pipes with your credentials and save the JSON output to files in the `docs` directory of this cloned project. Each of your JSON files should be named following the convention `*tumblr*.json`. For example: 

    docs/tumblr-likes.json
    docs/tumblr-posts-1.json
    docs/tumblr-posts-2.json
    ...

## Edit 

TATE uses **Gmail** to create a new Evernote note for each post in your JSON files.

Why Gmail and not OAuth? [Read the rationale.](https://github.com/mattnorris/tate/wiki/FAQs)

Edit the following constants in `tate.py` to use your Gmail account and Evernote email address. 

    USER = 'GMAIL_ADDRESS'
    PASSWORD = 'GMAIL_PASSWORD'
    RECIPIENT = 'EVERNOTE_EMAIL_ADDRESS'

## Run

    python tate.py 
