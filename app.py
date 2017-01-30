from flask import Flask, jsonify, request, abort, url_for
from flask_mongoengine import MongoEngine

import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth1

import threading
import atexit
import datetime

# create the application object
from flask import render_template

app = Flask(__name__)
app.config.from_object(__name__)

kidsHandler = threading.Thread()
KIDS_POOLING = 60*5

translatorHandler = threading.Thread()
TRANSLATOR_POOLING = 60*8

storiesHandler = threading.Thread()
STORIES_POOLING = 60*10

LANGUAGE_CODES = ['pt', 'nl']

# db Stuff
app.config['MONGODB_SETTINGS'] = {
    'db': 'TranslatedHN',
}

db = MongoEngine(app)

# Model
class Story(db.Document):
    by = db.StringField(max_length=100)
    descendants = db.IntField()
    hn_id = db.IntField()
    score = db.IntField()
    time = db.IntField()
    title = db.StringField(max_length=300)
    # TODO:modify this to a reference type
    type = db.StringField(max_length=50)
    url = db.StringField(max_length=300)
    kids = db.ListField(db.IntField())
    parent = db.IntField()
    text = db.StringField(max_length=5000)


STATES = ('ToDo', 'Asked', 'Processed')


class StoryTranslated(db.Document):
    state = db.StringField(max_length=12, choices=STATES)
    title = db.StringField(max_length=300)
    parent_story = db.ReferenceField(Story)
    language_code = db.StringField(max_length=2)
    #ToDo: Add time to filter old, unresolved translations

# Utilities
def serialize_story(story):
    # check if story exists on db
    story_check = Story.objects(hn_id=story['id'])

    # create the model
    if len(story_check) == 0:
        model_story = Story(
            by=story['by'],
            descendants=story['descendants'],
            hn_id=story['id'],
            score=story['score'],
            time=story['time'],
            title=story['title'],
            type=story['type']
        )
        if 'url' in story:
            model_story.url = story['url']

        if 'kids' in story:
            model_story.kids = story['kids']

        model_story.save()

def serialize_kid(kid):
    # check if story exists on db
    kid_check = Story.objects(hn_id=kid['id'])

    # create the model
    if len(kid_check) == 0:
        model_kid = Story(
            by=kid['by'],
            hn_id=kid['id'],
            time=kid['time'],
            type=kid['type'],
            parent=kid['parent'],
            text=kid['text']

        )
        if 'kids' in kid:
            model_kid.kids = kid['kids']
        
        model_kid.save()
            


def get_topmost_stories():
    # call HN API
    try:
        request_topmost_stories = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty')
        topmost_stories_ids_json = request_topmost_stories.json()
        # get top most 10 + 2 stories

        for story_index in range(0, 12):
            request_story = requests.get('https://hacker-news.firebaseio.com/v0/item/' +
                                     str(topmost_stories_ids_json[story_index]) + '.json?print=pretty')
            story = request_story.json()
            # serialize on local db
            serialize_story(story)

    except Exception as e:
        print e

    print "topmost stories handler finished"
    storiesHandler = threading.Timer(TRANSLATOR_POOLING, get_topmost_stories, ())
    storiesHandler.start()

def interrupt():
    global kidsHandler
    kidsHandler.cancel()

    global translatorHandler
    translatorHandler.cancel()

def get_kid_from_hn(kid_id):

    try:
        kid_check = Story.objects(hn_id=kid_id)

        if len(kid_check) == 0:

            request_kid = requests.get('https://hacker-news.firebaseio.com/v0/item/' +
                                   str(kid_id) + '.json?print=pretty')

            kid = request_kid.json()
            # serialize on local db
            serialize_kid(kid)
        else:
            kid = kid_check[0]


        #handles their own kids
        if 'kids' in kid:
            for k in kid['kids']:
                get_kid_from_hn(k)


    except Exception as e:
        print e

def get_kids_from_hn():
    #get topmost stories from today with highest score from db
    d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
    stories = Story.objects(time__gte=today_timestamp)

    for s in stories:
        kids = s.kids
        for k in kids:
            get_kid_from_hn(k)

    print "comments handler finished"
    kidsHandler = threading.Timer(KIDS_POOLING, get_kids_from_hn, ())
    kidsHandler.start()

def start_get_kids():

    global kidsHandler
    kidsHandler = threading.Timer(KIDS_POOLING, get_kids_from_hn, ())
    kidsHandler.start()


def ask_translation(story, language_code):
    try:
        #check if this translation is already done or asked
        translation_check = StoryTranslated.objects(parent_story=story.id)
        ask_for = False
        if len(translation_check) == 0:
            ask_for = True
        elif translation_check[0].state == 'ToDo':
            ask_for = True
            translation_check = translation_check[0]

        if ask_for:

            # headers = {'Authorization': 'ApiKey', 'backendchallenge': '711b8090e84dcb4981e6381b59757ac5c75ebb26'}# {"Content-Type": "application/json"}
            headers = {'Authorization': 'ApiKey backendchallenge:711b8090e84dcb4981e6381b59757ac5c75ebb26', "Content-Type": "application/json"}

            url = 'https://sandbox.unbabel.com/tapi/v2/translation/'
            payload = {'text': story.title, 'target_language': language_code, "text_format": 'text'}

            r = requests.post(url, data=payload, headers=headers)


            # r = requests.post(url, data=payload, headers=headers,
            #                   auth=('backendchallenge', '711b8090e84dcb4981e6381b59757ac5c75ebb26'))

            if 'uid' in r:
                #update or create translated story
                translation_check = StoryTranslated(
                    state='Asked',
                    parent_story=story.id,
                    uid=r.uid,
                    language_code=language_code
                )
                translation_check.save()

            else:
                translated = StoryTranslated(
                state='ToDo',
                parent_story=story.id,
                language_code=language_code,
                title="##PROCESSING##"
            )
            translated.save()
    except Exception as e:
        print e


def get_translation(story_translated):
    try:
        if story_translated.state == 'Asked':
            headers = {'Authorization': 'ApiKey',
                       'backendchallenge': '711b8090e84dcb4981e6381b59757ac5c75ebb26',
                       "Content-Type": "application/json"
                       }
            url = 'https://sandbox.unbabel.com/tapi/v2/translation/' + story_translated.uid
            # payload = {'text': story.title, 'target_language': language_code, "text_format": 'text'}

            r = requests.post(url, headers=headers)

            if 'status' in r:
                if r['status'] == "completed":
                    story_translated.title_translated = r['translatedText']
                    story_translated.state = 'Processed'
                    story_translated.save()

    except Exception as e:
        print e


def get_translations():
    try:
        #get stories to translate
        d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
        today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
        stories = Story.objects(time__gte=today_timestamp, type='story')

        for l in LANGUAGE_CODES:
            for s in stories:
                ask_translation(s, l)
        todo_translated_stories = StoryTranslated.objects(state='ToDo')
        for ts in todo_translated_stories:
            get_translation(ts)

    except Exception as e:
        print e

    print "translations handler finished"
    translatorHandler = threading.Timer(TRANSLATOR_POOLING, get_translations, ())
    translatorHandler.start()


def start_get_translations():

    global translatorHandler
    translatorHandler = threading.Timer(1, get_translations, ())
    translatorHandler.start()


def start_get_topstories():

    global storiesHandler
    storiesHandler = threading.Timer(1, get_topmost_stories, ())
    storiesHandler.start()


# Views
@app.route('/')
def get_translated_hn():
    url_for('static', filename='app.js')
    # myStory = Story(by='rgilpt', descendants=2, hn_id=69).save()
    d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
    stories = Story.objects(time__gte=today_timestamp, type='story')
    stories = stories.order_by('-score')[0:10]

    return render_template('show_news.html', stories=stories)


@app.route('/dashboard')
def get_dashboard():
    url_for('static', filename='app.js')
    # myStory = Story(by='rgilpt', descendants=2, hn_id=69).save()
    d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
    stories = Story.objects(time__gte=today_timestamp, type='story')
    dashboard_info = []
    for s in stories:
        dashboard_line = {'original': s.title}
        for lc in LANGUAGE_CODES:
            story_translated = StoryTranslated.objects(parent_story=s, language_code=lc)
            if len(story_translated) > 0:
                dashboard_line[lc] = story_translated[0].state
        dashboard_info.append(dashboard_line)

    return render_template('dashboard.html', dashboard_info=dashboard_info)


@app.route('/api/v1.0/translated_stories/', methods=['GET'])
def get_translated_stories():
    if not request.args or not 'language_code' in request.args:
        abort(400)

    d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
    stories = Story.objects(time__gte=today_timestamp, type='story')
    stories = stories.order_by('-score')[0:10]

    final_stories = []
    for s in stories:
        story_translated = StoryTranslated.objects(parent_story=s, language_code=request.args['language_code'])
        if len(story_translated) > 0:
            final_stories.append(story_translated[0])

    return jsonify({'stories': final_stories})

@app.route('/api/v1.0/stories/', methods=['GET'])
def get_stories():
    d = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    today_timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()
    stories = Story.objects(time__gte=today_timestamp, type='story')
    stories = stories.order_by('-score')[0:10]

    return jsonify({'stories': stories})


if __name__ == "__main__":
    atexit.register(interrupt)

    # get_topmost_stories()
    start_get_topstories()
    start_get_kids()
    start_get_translations()
    app.run()
