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
    """Class to webscrap content on Twitter

    Things to know :
    - In headless mode, we need to use Firefox browser from Selenium to make it works ( Chrome doesn't work)"""

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

        self.class_time = 'css-4rbku5 css-18t94o4 css-901oao r-14j79pv r-1loqt21 r-1q142lx r-37j5jr r-a023e6 ' \
                          'r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0'  # time
        self.class_twits = 'css-901oao r-18jsvk2 r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0'

        self.buffer_date_ = 40
        self.date_ = ''  # date if different from today in the Xpath
        self.date__ = '' #list of date set in method `self.buffer_date()` to find the posts with the date we want
        self.twits = ""  # contains the twit fetched from Twitter (text, date, directional ie bullish or bearish)
        self.twit_dictionary = {}  # dictionary with information from twits

    def __call__(self):
        """built-in function to initialize values"""

        self.buffer_date()
        self.date_to_search = '//a[@class="{}" and ({})]'.format(self.class_time, self.date__)
        # elements we are returning to analyse the comment itself
        self.posts_to_return = "//div[@class='{}']".format(self.class_twits)

    @pm.decorator_timer(2) #2 is for twitter in `self.comment_source` in `initialise.py`
    def webscrap(self):
        """Performs all the method necessary to webscrap the content on twitter and analyse the mood of the
        comments"""

        self.twits = "" #we need to reinitialise the list which contains the comments everytime we fetch data
                        #for a new stock
        self.stock_endpoint = ''.join(['https://twitter.com/search?q=%24', self.init.current_stock,
                                       '&src=typed_query&f=live'])
        self.twits = pm.webscrap_content(driver=self.init.driver_ff,posts_to_return=self.posts_to_return,
                                               end_point=self.stock_endpoint,pause_time=self.init.pause_time,
                                         date_to_search = self.date_to_search,is_twitter= True)
        return self.write_values()


    def convert_time(self,time_ago):
        """Method to convert time readable in the Xpath in Selenium.

        Parameters
        ----------
        `time_ago` : int
            Time ago we want to webscrap the data
        """

        now = datetime.now()  # get the current datetime, this is our starting point
        # datetime according to the number of the days ago we want
        start_time = now - timedelta(hours=(time_ago))

        #less than 24 hours ago, the format for dates is different than more than 24 hours.
        #Ex: It will show as '23h' (for 23 hours ago) and 'Nov 29' (example) for more than 24 hours

        if time_ago < 24:
            self.date_ = ''.join([str(time_ago),'h'])
        else:
            # Write the day in Xpath format for Twitter
            text = [str(start_time.strftime('%b')), str(start_time.day)]
            self.date_ = (' '.join(text))

    def buffer_date(self):
        """ Method to make a list of date we can click on. It's a buffer to make sure that we don't scroll forever.
         Ex : We are looking for 'Nov 10' on a stock, but the volume is low, we may find data before, but not exactly
         on November 10. It depends on the size of the buffer `self.buffer_date_`
        """

        iteration = 1
        j=0
        tempo_time = self.init.time_ago
        while iteration < self.buffer_date_:
            #less than 24 hours
            if (iteration - 1 + self.init.time_ago)<24:
                self.convert_time(iteration-1+self.init.time_ago)
            else:
                self.convert_time(j*24 + 24)  # multiply iteration by 24 to have in day
                j+=1

            if iteration == 1:
                self.date__ += ''.join(['@aria-label = ','"', self.date_, '"'])
            else:
                self.date__ += ''.join([' or @aria-label = ','"', self.date_, '"'])
            iteration += 1

    def loop_twits(func):
        """Decorator to loop throught the comments that we webscrap"""

        def wrapper_(self):
            for twit in self.twits:
                self.twit_dictionary = {}  # dictionary with information from twits
                func(self,twit)
            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.drop_duplicates\
                (subset=self.init.columns_sentiment[0], keep="first",ignore_index=True)
            return self.init.pd_stock_sentiment
        return wrapper_

    @loop_twits
    def write_values(self,twit):
        """Method to determine if mood of each comment (positive, negative) with a score between -1 and 1
         (-1 being the most negative and +1 being the most positive and write different values in the
         pandas DataFrame `self.pd_stock_sentiment`"""

        self.init.pd_stock_sentiment = pm.write_values(comment = twit,pv = self.init,source = 2,
                                                       model = self.init_sentiment,dict_ = self.twit_dictionary)