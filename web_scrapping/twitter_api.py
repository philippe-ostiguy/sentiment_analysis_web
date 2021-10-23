#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-
###############################################################################
#
#  The MIT License (MIT)
#  Copyright (c) 2021 Philippe Ostiguy
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

"""It's the module to get info and make API calls to Twitter
PROBLÈMES:
L'API de Twitter permet seulement d'aller chercher jusqu'au 7 derniers jours les tweets max (avant, pas possible)
- Problème avec la version 2 (API de Twitter). Impossible d'aller chercher des tickers avec le cashtag.
Voir ce lien : https://stackoverflow.com/questions/66391136/how-to-solve-operator-error-on-twitter-search-api-2-0/68745951#68745951
et ic : https://twittercommunity.com/t/reference-to-invalid-operator-cashtag-operator-is-not-available-in-current-product-or-product-packaging/141990/7

- Problème avec la version 1 (API de Twitter). Impossible de dire un début de date. Donc, on aura seulement un maximum
de 100 tweets à partir du moment de la requête (paramètre `count` peut aller à max 100).
On peut avoir des tweets à partir seulement de `since_id` (paramètre) qui est selon l'ID d'un tweet
https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/api-reference/get-search-tweets


"""

import requests
from datetime import datetime, timedelta,time
from dateutil.relativedelta import relativedelta
from decouple import config
import time
import re
import pandas as pd

def delta_date(start_date,end_date):
    """Function that returns the number of days between 2 dates """

    return abs((datetime.strptime(start_date, "%Y-%m-%d") - datetime.strptime(end_date, "%Y-%m-%d")).days)

def get_data(dict,keys_):
    """Function that stores the data from a dictionary with the specific keys in a a new dictionary
    Parameters
    ----------
    `dict` : dictionary
        API's endpoint parameter
    `keys_` : list
        list of the keys in the dictionary we want to store in the new_didt
    """
    new_dict = {}
    for key in keys_:
        new_dict[key]=dict[key]
    return new_dict

class TwitterApi_():
    """Class to make API calls to Twitter API

    With the free version you can get up to the last 7 days of tweets and maximum results of 100 tweets per API call
    https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference

    On oublie l'API de Twitter, car on ne peut pas faire de recherche sur des symboles ($). Ce n'est pas supporté
    pour le public, seulement pour 'académique'
    """

    def __init__(self):
        """
        Attributes
        ----------
        `self.twitter_api` : str
            twitter API bearer token to acces "my" twitter application
        `self.date_format` : str
            date format for the Twitter API's call. Required by Twitter
        `self.headers` : str
            headers for the API's call
        `self.params` : str
            parameters for the API's call
        `self.endpoint` : str
            API's endpoint parameter
        `self.query` : str
            API's query parameter
        `self.max_results` : int
            API's max results parameter. Default and max by Twitter is 100
        `self.days_ago` : str
            number of days ago from now that we want tweets. Max days ago is 7
        `self.nb_minutes` : int
            number of minutes that we collect data per API call. Hard to determine but from observations it should not
            be above 5 minutes
        """

        self.twitter_bearer = config('BEARER_TOKEN_TWITTER')
        self.date_format = '%Y-%m-%dT%H:%M:%SZ'

        #version 2 API Twitter
        self.endpoint = 'https://api.twitter.com/2/tweets/search/recent' #version 2
        self.query = 'SPY' + ' lang:en'

        self.max_results = 100
        self.days_ago = 30 #à changer après = mettre max 7
        self.nb_minutes = 15

        #version 2 API twitter
        self.params = {
            'query' : self.query,
            'max_results' : self.max_results,
            'tweet.fields' : 'created_at,lang,text'
        }

        self.headers = {'authorization': f'Bearer {self.twitter_bearer}'}
        self.df = pd.DataFrame() #dataframe to store the tweets


    def __call__(self):
        self.get_tweets_()
        t = 5

    def get_data(self,tweet):
        data = {
            'id': tweet['id'],
            'created_at': tweet['created_at'],
            'text': tweet['full text']
        }
        return data

    def get_previous_time(self,now, mins):
        """ """
        now = datetime.strptime(now, self.date_format)
        back_in_time = now - timedelta(minutes=mins)
        return back_in_time.strftime(self.date_format)

    def get_tweets_(self):
        now = datetime.now()  # get the current datetime, this is our starting point
        start_time = now - timedelta(minutes=self.days_ago)  # datetime according to the number of the days ago we want
        now = now.strftime(self.date_format)  # convert now datetime to format for API

        while True:
            if datetime.strptime(now, self.date_format) < start_time:
                # if we have reached `self.days_ago` days ago, break the loop
                break

            pre_now = self.get_previous_time(now, self.nb_minutes)  # get `self.nb_minutes` minutes before 'now'

            # assign from and to datetime parameters for the API
            self.params['start_time'] = pre_now
            self.params['end_time'] = now
            response = requests.get(self.endpoint,
                                    params=self.params,
                                    headers=self.headers)  # send the request
            now = pre_now  # move the new window (now) `self.nb_minutes` before 'now'

            # iteratively append our tweet data to our dataframe
            for tweet in response.json()['data']:
                row = self.get_data(tweet)
                self.df = self.df.append(row, ignore_index=True)