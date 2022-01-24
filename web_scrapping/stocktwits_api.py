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
    """Class to webscrap content on Stocktwits.

     Things to know:
     - Method `self.buffer_date_` is built to search post published on the same date. Some developing may be required
     if we want to search from a date different from today.
    - In headless mode, we need to use Chrome browser from Selenium to make it works (Firefox doesn't work)

     """

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
            Number of hours in the past we want to webscrape the data. At the moment, we search for post
             published during the same day. If we want to search previous date, we would need to adjust the function
             `self.buffer_date_()`
        `self.stock_endpoint` : str
            Endpoint of the stock we want to webscrap
        `self.buffer_date_` : int
            Size of the buffer to search date for in function `self.buffer_date_`
        """

        #We should touch these data. They come from the classes where we initialize the data
        self.init = init #variable for the class containing the global variables for the project
        # variable for the class with the model/transformer to analyse twits/comments
        self.init_sentiment = init_sentiment

        self.stock_endpoint = ''

        self.class_time = 'st_28bQfzV st_1E79qOs st_3TuKxmZ st_1VMMH6S' #time
        self.class_twits = 'st_29E11sZ st_jGV698i st_1GuPg4J st_qEtgVMo st_2uhTU4W'
        self.class_directional = 'lib_XwnOHoV lib_3UzYkI9 lib_lPsmyQd lib_2TK8fEo' #bull or bear

        self.date_ = '' #date if different from today in the Xpath
        self.date__ = '' #list of date set in method `self.buffer_date()` to find the posts with the date we want
        self.stock_twits = "" #contains the twit fetched from stocktwits (text, date, directional ie bullish or bearish)
        self.twit_dictionary = {}  # dictionary with information from twits
        self.buffer_date_ = 40

        self.which_driver = 'chrome' #driver we takes to webscrap the data, chrome for twitter should be used


    def __call__(self):
        """built-in function to initialize values"""

        self.buffer_date()
        #class to check if the page is not empty on stocktwit
        self.stocktwit_class = '//a[@class="{}"]'.format(self.class_time)
        self.date_to_search = '//a[@class="{}" and ({})]'.format(self.class_time, self.date__)
        # elements we are returning to analyse the comment itself
        self.posts_to_return = "//div[@class='{}']".format(self.class_twits)

    @pm.decorator_timer(1) #1 is for stocktwits in `self.comment_source` in `initialise.py`
    def webscrap(self):
        """Performs all the method necessary to webscrap the content on stocktwits and analyse the mood of the
        comments"""

        self.stock_twits = ""
        self.stock_endpoint = ''.join(['https://stocktwits.com/symbol/',self.init.current_stock])
        self.stock_twits = pm.webscrap_content(driver_parameters=  self.init.driver_parameters,
                                               end_point=self.stock_endpoint, pause_time=self.init.pause_time,
                                               date_to_search = self.date_to_search,which_driver = self.which_driver,
                                               posts_to_return=self.posts_to_return,
                                               stocktwit_class = self.stocktwit_class)
        return self.write_values()

    def convert_time(self, search_time, is_today):
        """Method to convert time readable in the Xpath in Selenium.
        """

        text = ''
        # current search time is today
        if is_today:
            if search_time.hour >= 12:
                period_of_day = ' PM'
            else:
                period_of_day = ' AM'

            hour = search_time.hour
            # midnight
            if hour == 0:
                hour = 12

            # transform non 'am' 'pm to 'am'/'pm'
            if hour > 12:
                hour -= 12

            # need to add a zero at the beginning if the hour is below 10
            if hour < 10:
                hour_ = '0' + str(hour)
            elif hour >= 10:
                hour_ = str(hour)

            minute = search_time.minute
            if minute < 10:
                minute_ = '0' + str(minute)
            else:
                minute_ = str(minute)

            text = [hour_, ':', minute_, period_of_day]
            self.date_ = ''.join(text)

        else:
            # Write the day in Xpath format for stocktwits
            text = [str(search_time.month), str(search_time.day), search_time.strftime('%y')]
            self.date_ = ('/'.join(text))

    def buffer_date(self):
        """ Method to make a list of date we can click on. It's a buffer to make sure that we don't scroll forever.
         Ex : We are looking for 'Nov 10' on a stock, but the volume is low, we may find data before, but not exactly
         on November 10. It depends on the size of the buffer `self.buffer_date_`

         If we are looking for something the same day, we wll write a buffer minutes by minutes from where we want to
         search until yesterday. Ex : If we are looking for something 1 hour ago and it's on the same day,
         then we will have 1 hour ago, 1 hour and 1 minute ago, 1 hour and 2 minutes ago

         If we are looking for something before today (yesterday or earlier), we have a buffer
         in term of datesEx: If yesterday is Nov 20, then all posts from today won't
         have a date in the class time (only hours and minutes ago it was published. However, starting from November
         20 and before, we will see 'Nov 20', 'Nov 19', 'Nov 18', etc.
        """

        now = datetime.now()
        search_time = now - timedelta(hours=self.init.time_ago)

        #check if we search for same day or not
        if search_time.day == now.day:
            same_day = True
            #set date until where we have buffer to yesterday
            delta_ = 1 #get buffer for every minute
            furthest_date = now - timedelta(days=1)
        else :
            same_day= False
            #set date until where we have buffer depending on `self.buffer_date_` and `time_ago`
            delta_ = 1*24*60 #number of minutes in 1 day to get 1 buffer per day
            t = timedelta(hours=(self.buffer_date_*24 + self.init.time_ago))
            furthest_date = now - timedelta(hours=(self.buffer_date_*24 + self.init.time_ago))

        iteration = 1
        #we need to write minute by minute to search time in stocktwits as time in post show the minutes.
        #Ex : 10:05 AM
        while(furthest_date.day != search_time.day or furthest_date.month != search_time.month or
              furthest_date.year != search_time.year):
            self.convert_time(search_time,same_day)
            if iteration == 1:
                self.date__ += ''.join(['contains(text(),', '"', self.date_, '")'])
            else:
                self.date__ += ''.join([' or contains(text(),', '"', self.date_, '")'])

            search_time-=timedelta(minutes=delta_)
            iteration +=1


    def loop_twits(func):
        """Decorator to loop throught the comments that we webscrap"""

        def wrapper_(self):
            for twit in self.stock_twits:
                self.twit_dictionary = {}
                # keep the text after the symbol which is the opinion expressed
                bullish = 'Bullish'
                bearish = 'Bearish'

                # check if it contains bullish or bearish or not in the class
                # then we are able to extract the twit only

                twit_directional = twit.split('\n')[1:2][0]
                if bullish in twit_directional or bearish in twit_directional:
                    twit_tempo = twit.split('\n', 3)[3:4][0]
                    self.twit_dictionary[self.init.columns_sentiment[2]] =twit_directional

                else:
                    twit_tempo = twit.split('\n', 2)[2:3][0]
                    self.twit_dictionary[self.init.columns_sentiment[2]] = ''

                func(self, twit_tempo)

            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.drop_duplicates\
                (subset=self.init.columns_sentiment[0], keep="first",ignore_index=True)
            return self.init.pd_stock_sentiment
        return wrapper_


    @loop_twits
    def write_values(self,twit):
        """Method to determine if mood of each comment (positive, negative) with a score between -1 and 1
         (-1 being the most negative and +1 being the most positive and write different values in the
         pandas DataFrame `self.pd_stock_sentiment`"""

        self.init.pd_stock_sentiment = pm.write_values(comment = twit,pv = self.init,
                                                     model = self.init_sentiment,source = 1,
                                                       dict_ = self.twit_dictionary)