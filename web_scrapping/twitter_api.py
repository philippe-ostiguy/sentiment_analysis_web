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

"""It's the module to webscrap data on Twitter"""

import requests
from datetime import datetime, timedelta, time
import time
from initialize import InitStockTwit
import re
import pandas as pd
import web_scrapping.package_methods as pm
import os
import sentiment_analysis as sa
from collections import defaultdict
import web_scrapping.package_methods as pm


class TwitsApi():
    """Class to webscrap content on Twitter"""

    def __init__(self, init, init_sentiment):

        """
        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project

        Attributes
        ----------
        `self.class_time` : str
            Name of the class in Twitter containing the published time of a twit
        `self.class_twits` : str
            Name of the class in Twitter containing the twits (text, directional))
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. The value must be 24 hours or more or it
            the webscrapping of data will not work properly. If we want to set a value between 1 hour and 24 hours, we
            must review the function `self.convert_time()`
        `self.stock_endpoint` : str
            Endpoint of the stock we want to webscrap
        `self.buffer_date_` : int
            Size of the buffer to search date for in function `self.buffer_date_`
        """

        # We should touch these data. They come from the classes where we initialize the data
        self.init = init  # variable for the class containing the global variables for the project
        # variable for the class with the model/transformer to analyse twits/comments
        self.init_sentiment = init_sentiment

        self.stock_endpoint = 'https://twitter.com/search?q=%24' + 'gib' + '&src=typed_query&f=live'
        self.class_time = 'css-4rbku5 css-18t94o4 css-901oao r-14j79pv r-1loqt21 r-1q142lx r-37j5jr r-a023e6 ' \
                          'r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0'  # time
        self.class_twits = 'css-901oao r-18jsvk2 r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0'

        self.buffer_date_ = 10
        self.date_ = ''  # date if different from today in the Xpath
        self.twits = ""  # contains the twit fetched from Twitter (text, date, directional ie bullish or bearish)
        self.twit_dictionary = {}  # dictionary with information from twits

    def __call__(self):

        self.convert_time()
        self.date_to_search = '//a[@class="{}" and @aria-label="{}"]'.format(self.class_time, self.date_)
        # elements we are returning to analyse the comment itself
        self.posts_to_return = "//div[@class='{}']".format(self.class_twits)

        self.twits = pm.webscrap_content(driver=self.init.driver,posts_to_return=self.posts_to_return, date_=self.date_,
                                               end_point=self.stock_endpoint,class_time=self.class_time,
                                               pause_time=self.init.pause_time,date_to_search = self.date_to_search)
        return self.analyse_content()

    def convert_time(self):
        """Method to convert time readable in the Xpath in Selenium.
        """

        now = datetime.now()  # get the current datetime, this is our starting point
        # datetime according to the number of the days ago we want
        start_time = now - timedelta(hours=self.init.time_ago)

        # Write the day in Xpath format for Twitter
        text = [str(start_time.strftime('%b')), str(start_time.day)]
        self.date_ = (' '.join(text))
        t = 5

    def buffer_date(self):
        """ Method to make a list of date we can click on. It's a buffer to make sure that we don't scroll forever.
         Ex : We are looking for 'Nov 10' on a stock, but the volume is low, we may find data before, but not exactly
         on November 10. It depends on the size of the buffer `self.buffer_date_`
        """

        i = 1
        while i < self.buffer_date_:
            if i == 1:
                self.rejected_replies_list += ''.join([' and not(./div/p/text() = ', '"', str(i), ' more reply', '")'])
            else:
                self.rejected_replies_list += ''.join(
                    [' and not(./div/p/text() = ', '"', str(i), ' more replies', '")'])

            i += 1

    def analyse_content(self):
        """Method to analyse content on Twitter"""

        for twit in self.twits:

            # remove all unescessary text (emoji, \n, other symbol like $)
            twit_tempo = pm.text_cleanup(twit_tempo)
            # writing the comments in the dictionary
            self.twit_dictionary[self.init.columns_sentiment[0]] = twit_tempo
            # writing the sentiment analysis result in the dictionary
            self.twit_dictionary[self.init.columns_sentiment[1]] = self.init_sentiment.roberta_analysis(twit_tempo)

            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.append(self.twit_dictionary, ignore_index=True)

        return self.init.pd_stock_sentiment