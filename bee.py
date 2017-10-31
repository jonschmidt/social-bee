import praw, operator

from praw.models import MoreComments
import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
from bittrex3.bittrex3 import Bittrex3

# settings.py
from os.path import join, dirname
from dotenv import load_dotenv

import datetime
import os

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ['FIREBASE_DATABASE_URL']
})

db = firestore.Client()
new_city_ref = db.collection('cities').document()
doc_ref = db.collection('social').document()

reddit = praw.Reddit(client_id=os.environ['R_ID'],
                     client_secret=os.environ['R_S'],
                     user_agent='my user agent')

bittrex = Bittrex3(os.environ['BT_K'],os.environ['BT_S'])

counts = {}
currencies = {}

for value in bittrex.get_currencies().get("result"):
    if len(value.get("Currency")) > 1:
        counts[value.get("Currency")] = 0
        currencies[value.get("Currency")] = value

for submission in reddit.subreddit('cryptoMarkets+ethTrader+cryptoCurrency+BitcoinMarkets').search('flair:"Discussion"','new','lucene', 'day'):
    for key in counts.keys():
        counts[key] = counts[key] + submission.selftext.count(
            currencies[key].get("CurrencyLong")) + submission.selftext.count(currencies[key].get("Currency"))
        for comment in submission.comments.list():
            if isinstance(comment, MoreComments):
                continue
            counts[key] = counts[key] + comment.body.count(
                currencies[key].get("CurrencyLong")) + comment.body.count(currencies[key].get("Currency"))

sorted_counts = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

doc_ref.set({
            'timestamp': datetime.datetime.now(),
            'reddit': counts
        })

for key in sorted_counts:
    if counts[key[0]] > 0:
        print("[" + currencies.get(key[0]).get("Currency") + "] " + str(counts[key[0]]))

