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

"""Module to webscrap data on Reddit (wallstreetbets)"""


from datetime import datetime, timedelta, time, date
import time
import pandas as pd
import os
import web_scrapping.package_methods as pm
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import web_scrapping.package_methods as pm
from pmaw import PushshiftAPI


class RedditApi_():
    """Class to webscrap data on Reddit using Selenium. It stores it in a pandas dataFrame.
    Things to know :
    - It's made for an analysis on a daily basis (by default, but can be changed it we modify `self.time_ago`
    - From Tuesday to Friday, we try to get the last 24 hours of comments
    - On Monday, we get the comments posted during the weekend
    """

    def __init__(self,init,init_sentiment):
        """
        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project
        `init_sentiment` : cls
            class from the module `twits_analysis` with the Twitter Roberta based transformer model already initialized
            and ready to perform sentiment analysis

        Attributes
        ----------
        `self.init.current_stock` : str
            current stock we webscrap

        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. This value must be 1 hour or more as the time
            format in Reddit is in hours (under 24 hours) and days (24 hours or more after the post was created).
            By default, the value is 24, and should not be changed. If it is changed, the funciton `self.set_time_ago()`
            should be reviewed.
            The program is made to search the last 24 hours and
            it operates this way. Ex: the function `self.set_time_ago()` changes `self.time_ago` depending if we are on
            Monday or on a US Stock holiday and will fetch accordingly.
        """

        super().__init__()
        #We should touch these data. They come from the classes where we initialize the data
        self.init = init #giving the values of class `init` to `self.init` variable (pv for project variables)
        self.roberta = init_sentiment #giving the values of class `init_sentiment` to `self.roberta` variable

        self.api = PushshiftAPI() #the pushift API
        self.reddit_comments= [] #list that contains the comments (text only)

    @pm.decorator_timer(0) #0 is for reddit in `self.comment_source` in `initialise.py`
    def webscrap(self):
        """Method that get the comments on reddit using Pushift API and pmaw (wrapper around Pushift)"""

        current_time = datetime.now()
        beggining_time = current_time - timedelta(hours = self.init.time_ago)

        self.before = int(current_time.timestamp()) #this is actually the time
        self.after = int(beggining_time.timestamp()) #this is the time where we start to webscrap

        comments = self.api.search_comments(subreddit=self.init.subreddit, limit=self.init.limit, before=self.before,
                                       after=self.after)
        self.reddit_comments += [comment['body'] for comment in comments if comment['body'] != ('[' + 'removed' + ']')]
        t = 5


    def loop_comments(func):
        """Decorator to loop throught the comments that we webscrap"""

        def wrapper_(self):
            self.reddit_dict_ = {}
            for comment in self.reddit_comments:
                # check if the post contains the stock (keywords) we are looking for
                is_breaking = False
                for stock,keywords in self.init.stock_dictionnary.items():
                    #while looping the dictionary with keywords, we check if we are the current stock
                    #that we want to get the comments
                    if stock == self.init.current_stock:
                        #check if the comment contains at least one of the keyword for this stock
                        for keyword in keywords:
                            if keyword in comment:

                                try :
                                    left_substring = comment.partition(keyword)[0][-1]
                                except:
                                    left_substring = '' #keyword at the beggining

                                try:
                                    right_substring = comment.partition(keyword)[2][0]
                                except:
                                    right_substring = '' #keyword at the end of sentence

                                #Make sure that the ticker is not followed or preceded by an alphanumeric character.
                                #Ex: ticker 'ED' could be preceded by 'F' which is 'FED' and not relevant to 'ED' ticker
                                if not left_substring.isalnum() and not right_substring.isalnum():
                                    func(self,comment)
                                    break # not analyzing the same post twice (in case we have more than 1 keyword)
                                    is_breaking = True
                        if is_breaking:
                            break


            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.drop_duplicates\
                (subset=self.init.columns_sentiment[0], keep="first",ignore_index=True)
            return self.init.pd_stock_sentiment
        return wrapper_

    @pm.decorator_timer(0) #0 is for reddit in `self.comment_source` in `initialise.py`
    @loop_comments
    def write_values(self,comment):
        """Method to determine the mood of each comment (positive, negative) with a score between -1 and 1
         (-1 being the most negative and +1 being the most positive and write different values in the
         pandas DataFrame `self.pd_stock_sentiment`"""

        self.init.pd_stock_sentiment = pm.write_values(comment = comment,pv = self.init,
                                                     model = self.roberta,source = 0,dict_ = self.reddit_dict_)