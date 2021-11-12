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

    """

    def __init__(self, init, init_sentiment):

        """
        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project

        Attributes
        ----------
        `self.pause_time` : long
            pause time when scrolling down the page and pause between manipulations on browser to load
        `self.class_time` : str
            Name of the class in Twitter containing the published time of a twit
        `self.class_twits` : str
            Name of the class in Twitter containing the twits (text, directional))
        `self.init.time_ago` : int
            Number of hours in the past we want to webscrape the data. The value must be 24 hours or more or it
            the webscrapping of data will not work properly. If we want to set a value between 1 hour and 24 hours, we
            must review the function `self.convert_time()`
        `self.stock_endpoint` : str
            Endpoint of the stock we want to webscrap
        """

        # We should touch these data. They come from the classes where we initialize the data
        self.init = init  # variable for the class containing the global variables for the project
        # variable for the class with the model/transformer to analyse twits/comments
        self.init_sentiment = init_sentiment
        self.time_ago = self.init.time_ago
        self.driver = self.init.driver  # driver to webscrap data on Selenium
        self.pause_time = self.init.pause_time

        self.stock_endpoint = 'https://twitter.com/search?q=%24' + 'gbi' + '&src=typed_query&f=live'
        self.class_time = 'st_28bQfzV st_1E79qOs st_3TuKxmZ st_1VMMH6S'  # time
        self.class_twits = 'st_29E11sZ st_jGV698i st_1GuPg4J st_qEtgVMo st_2uhTU4W'

        self.date_ = ''  # date if different from today in the Xpath
        self.twits = ""  # contains the twit fetched from Twitter (text, date, directional ie bullish or bearish)
        self.twit_dictionary = {}  # dictionary with information from twits

    def __call__(self):

        self.convert_time()
        self.stock_twits = pm.webscrap_content(driver=self.driver, class_twits=self.class_twits, date_=self.date_,
                                               end_point=self.stock_endpoint, class_time=self.class_time,
                                               pause_time=self.pause_time)
        return self.analyse_content()

    def convert_time(self):
        """Method to convert time readable in the Xpath in Selenium.
        """

        now = datetime.now()  # get the current datetime, this is our starting point
        start_time = now - timedelta(
            hours=self.init.time_ago)  # datetime according to the number of the days ago we want

        # Write the day in Xpath format for Twitter
        text = [str(start_time.month), str(start_time.day), start_time.strftime('%y')]
        self.date_ = ('/'.join(text))

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