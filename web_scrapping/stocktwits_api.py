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

"""It's the module to webscrap data on Stocktwits"""

import requests
from datetime import datetime, timedelta,time
import time
from initialize import InitStockTwit
import re
import pandas as pd
import web_scrapping.package_methods as pm
import os
import sentiment_analysis as sa
from collections import defaultdict
import web_scrapping.package_methods as pm

class StockTwitsApi():
    """Class to webscrap content on Stocktwits """

    def __init__(self,init,init_sentiment):

        """
        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project

        Attributes
        ----------
        `self.class_time` : str
            Name of the class in Stocktwits containing the published time of a twit
        `self.class_twits` : str
            Name of the class in Stocktwits containing the twits (text, directional)
        `self.class_directional` : str
            Name of the class with the directional (bull or bear)
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. The value must be 24 hours or more or it
            the webscrapping of data will not work properly. If we want to set a value between 1 hour and 24 hours, we
            must review the function `self.convert_time()`
        `self.stock_endpoint` : str
            Endpoint of the stock we want to webscrap
        """

        #We should touch these data. They come from the classes where we initialize the data
        self.init = init #variable for the class containing the global variables for the project
        # variable for the class with the model/transformer to analyse twits/comments
        self.init_sentiment = init_sentiment

        self.stock_endpoint = 'https://stocktwits.com/symbol/' + 'gib'
        self.class_time = 'st_28bQfzV st_1E79qOs st_3TuKxmZ st_1VMMH6S' #time
        self.class_twits = 'st_29E11sZ st_jGV698i st_1GuPg4J st_qEtgVMo st_2uhTU4W'
        self.class_directional = 'lib_XwnOHoV lib_3UzYkI9 lib_lPsmyQd lib_2TK8fEo' #bull or bear

        self.date_ = '' #date if different from today in the Xpath
        self.stock_twits = "" #contains the twit fetched from stocktwits (text, date, directional ie bullish or bearish)
        self.twit_dictionary = {}  # dictionary with information from twits
        
    def __call__(self):


        self.convert_time()
        self.date_to_search = '//a[@class="{}" and contains(text(),"{}")]'.format(self.class_time, self.date_)
        # elements we are returning to analyse the comment itself
        self.posts_to_return = "//div[@class='{}']".format(self.class_twits)
        self.stock_twits = pm.webscrap_content(driver=self.init.driver,posts_to_return=self.posts_to_return,
                                               end_point=self.stock_endpoint, class_time=self.class_time,
                                               pause_time=self.init.pause_time, date_to_search = self.date_to_search)
        return self.analyse_content()

    def convert_time(self):
        """Method to convert time readable in the Xpath in Selenium.
        """

        now = datetime.now()  # get the current datetime, this is our starting point
        start_time = now - timedelta(hours=self.init.time_ago)  # datetime according to the number of the days ago we want

        #Write the day in Xpath format for stocktwits
        text = [str(start_time.month), str(start_time.day),start_time.strftime('%y')]
        self.date_ = ('/'.join(text))

    def analyse_content(self):
        """Method to analyse content on stocktwits"""

        for twit in self.stock_twits:
            # keep the text after the symbol which is the opinion expressed
            bullish = 'Bullish'
            bearish = 'Bearish'

            #check if it contains bullish or bearish or not in the class
            #then we are able to extract the twit only
            if bullish in twit.text or bearish in twit.text:
                twit_tempo = twit.text.split('\n', 3)[3:][0]

            else:
                twit_tempo = twit.text.split('\n', 2)[2:][0]

            #remove all unescessary text (emoji, \n, other symbol like $)
            twit_tempo = pm.text_cleanup(twit_tempo)
            #if it's empty after cleaning, just continue, don't save/analyse the comment
            if twit_tempo == '':
                continue
            # writing the comments in the dictionary
            self.twit_dictionary[self.init.columns_sentiment[0]] = twit_tempo
            #writing the sentiment analysis result in the dictionary
            self.twit_dictionary[self.init.columns_sentiment[1]] = self.init_sentiment.roberta_analysis(twit_tempo)


            directional = re.search('\n(.*)\n', twit.text) #searching for 'bearish' or 'bullish' in the twit
            #If 'Bullish' or 'bearish', set the column 'directional to 'bullish or 'bearish accordindly.
            if (directional.group(1) == 'Bearish' or directional.group(1) == 'Bullish'):
                self.twit_dictionary[self.init.columns_sentiment[2]] = directional.group(1)


            #If the directional is not mentioned, then `directional.group(1)` is the 'time_published'
            else:
                self.twit_dictionary[self.init.columns_sentiment[2]] = ''


            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.append(self.twit_dictionary,ignore_index=True)

            
        return self.init.pd_stock_sentiment