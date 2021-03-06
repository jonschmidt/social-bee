import praw, operator
from praw.models import MoreComments

import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
import re
import datetime
import os
import requests  # To make HTTP requests
import urllib.request, json

# settings.py
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def get(url):
    print('Grabbing ' + url)
    r = requests.get(url)

    if r.status_code != 200:
        print('Failed to read ' + url + ', status code ' + str(r.status_code))
        exit()

    if not r.content:
        print('Failed to read ' + url + ', no content available')
        exit(r.status_code)

    return r.text


def fchan(currencies):
    counts = {}
    b = get('https://boards.4chan.org/biz')
    for k in currencies.keys():
        occurrences = sumOccurrences(b, currencies[k].get("name"))
        counts[k] = occurrences + sumOccurrences(b, currencies[k].get("symbol"))

    for x in range(2, 10):
        b = get('https://boards.4chan.org/biz/' + str(x))
        for k in currencies.keys():
            counts[k] = counts[k] + sumOccurrences(b, currencies[k].get("name")) + sumOccurrences(b, currencies[k].get("symbol"))

    return counts


def sumOccurrences(content, needle):
    return len(re.findall(r'\b{}\b'.format(needle), content))
    # return sum(len(re.findall(r'\b{}\b'.format(needle, line)) for line in f)


def rddt(currencies):
    counts = {}
    for k in currencies.keys():
        counts[k] = 0
    for submission in reddit.subreddit('cryptoMarkets+ethTrader+cryptoCurrency+BitcoinMarkets').search(
            'flair:"Discussion"', 'new', 'lucene', 'day'):
        for k in currencies.keys():
            counts[k] = counts[k] + submission.selftext.count(
                currencies[k].get("name")) + submission.selftext.count(currencies[k].get("symbol"))
            for comment in submission.comments.list():
                if isinstance(comment, MoreComments):
                    continue
                counts[k] = counts[k] + comment.body.count(
                    currencies[k].get("name")) + comment.body.count(currencies[k].get("symbol"))

    return counts


cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://peppermill-fd333.firebaseio.com'
})

db = firestore.Client()
new_city_ref = db.collection('cities').document()
doc_ref = db.collection('social').document()

reddit = praw.Reddit(client_id='I_VPG9ndTbFgCg',
                     client_secret='J8bahn7EHsyhVgV5MFBlER0OA9A',
                     user_agent='my user agent')
currencies = {}
with urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?limit=200") as url:
    data = json.loads(url.read().decode())
    for coin in data:
        currencies[coin["symbol"]] = coin

print('***4chan***')
fc = fchan(currencies)
for key in sorted(fc.items(), key=operator.itemgetter(1), reverse=True):
    if key[1] > 0:
        print("[" + key[0] + "] " + str(key[1]))

print('***Reddit***')
rd = rddt(currencies)
for key in sorted(rd.items(), key=operator.itemgetter(1), reverse=True):
    if key[1] > 0:
        print("[" + key[0] + "] " + str(key[1]))


doc_ref.set({
            'timestamp': datetime.datetime.now(),
            'reddit': rd,
            'fourchan': fc
        })