# Need more info? Check out the blogpost:
# how-to-make-a-bot-that-automatically-replies-to-comments-on-facebook-post

"""
NEED MORE INFO? CHECK OUT THE BLOGPOST
https://vandevliet.me/bot-automatically-responds-comments-facebook/
"""

import sqlite3
from time import sleep
import facebook
from PIL import Image
from io import BytesIO


APP_ID = 'TO FILL IN'
APP_SECRET = 'TO FILL IN'

PAGE_ID = 'TO FILL IN'
POST_ID_TO_MONITOR = 'TO FILL IN'
LONG_LIVED_ACCESS_TOKEN = 'TO FILL IN'

COMBINED_POST_ID_TO_MONITOR = '%s_%s' % (PAGE_ID, POST_ID_TO_MONITOR)


def make_new_profile_pic(img):
    im = Image.open(BytesIO(img))
    im = im.resize((480, 480))

    # background version
    # background = Image.open("./fcdk_overlay.png")
    #
    # background.paste(im, (100, 100))

    # background.show()
    # bytes_array = BytesIO()
    # background.save(bytes_array, format='PNG')
    # bytes_array = bytes_array.getvalue()
    # return bytes_array

    # foreground version
    foreground = Image.open("./tgr_overlay.png")
    foreground = foreground.resize((250, 250))
    im = im.resize((250, 250))

    im.paste(foreground, (0, 0), foreground)

    # im.show()
    bytes_array = BytesIO()
    im.save(bytes_array, format='PNG')
    bytes_array = bytes_array.getvalue()
    return bytes_array


def comment_on_comment(graph, comment):
    comment_id = comment['id']
    comment_from_name = comment['from']['name']
    comment_from_id = comment['from']['id']
    comment_message = comment['message']
    profile = None

    print("Let's comment!")
    # like the comment
    graph.put_like(object_id=comment_id)

    # profile info:
    photo = graph.get_connections(id=comment_from_id, connection_name='picture', height=480, width=480)
    # try to get first name, if it's a page there is not first_name
    try:
        profile = graph.get_object(comment_from_id, fields='first_name,last_name')
    except:
        pass

    # let's create our photo that we want to post
    photo_to_post = make_new_profile_pic(photo['data'])

    # first we upload it as an unpublished photo that doesn't appear as a story (in the newsfeed)
    posted_photo = graph.put_photo(
        image=photo_to_post,
        album_path='404896546596495/photos',
        no_story=True,
        published=False
    )

    # if it's a person that commented, we can use the first name
    if profile:
        graph.put_object(parent_object=comment_id, connection_name='comments',
                         message='Bozour %s. Hier is uwe foto, mijn gedacht!' % (profile['first_name']),
                         attachment_id=posted_photo['id']
                         )
    else:
        graph.put_object(parent_object=comment_id, connection_name='comments',
                         message='Hola copain. Hier is uwe foto, mijn gedacht!',
                         attachment_id=posted_photo['id']
                         )

    print('Edited and posted the photo of: %s' % comment_from_name)


def monitor_fb_comments():
    # create graph
    graph = facebook.GraphAPI(LONG_LIVED_ACCESS_TOKEN)
    # that infinite loop tho
    while True:
        print('I spy with my little eye...🕵️ ')
        sleep(5)

        # get the comments
        comments = graph.get_connections(COMBINED_POST_ID_TO_MONITOR,
                                         'comments',
                                         order='chronological')

        for comment in comments['data']:

            # if we can't find it in our comments database, it means
            # we haven't commented on it yet
            if not Posts().get(comment['id']):
                comment_on_comment(graph, comment)

                # add it to the database, so we don't comment on it again
                Posts().add(comment['id'])

        # while there is a paging key in the comments, let's loop them and do exactly the same
        # if you have a better way to do this, PRs are welcome :)
        while 'paging' in comments:
            comments = graph.get_connections(COMBINED_POST_ID_TO_MONITOR,
                                             'comments',
                                             after=comments['paging']['cursors']['after'],
                                             order='chronological')

            for comment in comments['data']:

                if not Posts().get(comment['id']):
                    comment_on_comment(graph, comment)
                    Posts().add(comment['id'])


# Mary had a little class
class Posts:
    def __init__(self):
        self.connection = sqlite3.connect('comments.sqlite3')
        self.cursor = self.connection.cursor()

    def get(self, id):
        self.cursor.execute("SELECT * FROM comments where id='%s'" % id)

        row = self.cursor.fetchone()

        return row

    def add(self, id):
        try:
            self.cursor.execute("INSERT INTO comments VALUES('%s')" % id)
            lid = self.cursor.lastrowid
            self.connection.commit()
            return lid
        except sqlite3.IntegrityError:
            return False

# started at the bottom, etc
if __name__ == '__main__':
    monitor_fb_comments()
