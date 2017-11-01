import praw, operator
from bittrex3.bittrex3 import Bittrex3
from praw.models import MoreComments

import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
import re
import datetime
import os
import requests  # To make HTTP requests


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
        occurrences = sumOccurrences(b, currencies[k].get("CurrencyLong"))
        if occurrences > 0 : print(occurrences)
        counts[k] = occurrences + sumOccurrences(b, currencies[k].get("Currency"))

    for x in range(2, 10):
        b = get('https://boards.4chan.org/biz/' + str(x))
        for k in currencies.keys():
            counts[k] = counts[k] + sumOccurrences(b, currencies[k].get("CurrencyLong")) + sumOccurrences(b, currencies[k].get("Currency"))

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
                currencies[k].get("CurrencyLong")) + submission.selftext.count(currencies[k].get("Currency"))
            for comment in submission.comments.list():
                if isinstance(comment, MoreComments):
                    continue
                counts[k] = counts[k] + comment.body.count(
                    currencies[k].get("CurrencyLong")) + comment.body.count(currencies[k].get("Currency"))

    return counts


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account.json'

cred = credentials.Certificate('service-account.json')

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

bittrex = Bittrex3('78dfc9260fe84b38b9e5674cf497d7e3', '8b13052f04a14d95b950f17c03a0fb71')

currencies = {}
for value in bittrex.get_currencies().get("result"):
    if len(value.get("Currency")) > 1:
        currencies[value.get("Currency")] = value

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