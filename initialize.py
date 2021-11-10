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
""" This is the module to initialize and set the values of variables used across the project

"""
import os
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta


class InitProject():
    """Class in which we decide the values of the variables (attribute) for the entire project"""
    pass

class InitNewsHeadline():
    """Class that initializes global value for the module for sentiment analysis of news headline.
    It also use general method to initialize values.
   """

    def __init__(self):
        """Built-in method to inialize the global values for sentiment analysis of news headline

        Attributes
        -----------
        `self.start.date` : str
            start date of the training period. Must be within the last year for the free version of FinHub. Format
            must be "YYYY-mm-dd"
        `self.end_date` : str
            end date of the training period. Format must be "YYYY-mm-dd"
        `self.ticker` : list
            tickers on which we want to perform the test. Can be one ticker in form of a list as well as a list
            of tickers like the s&p 500.
        `self.db_name` : str
            name of the sqlite3 database
        `self.web_scrap_name` : str
            name for the web_scrapping package (used for the folder directory name)
        `self.file_name` : str
            name of the file (db) including the directory. It takes into account the `self.start_date` and
            `self.end_date`
        `self.news_header` : list
            list containing the columns name returned (in order) by the FinnHub's API
        `self.start_date_` : datetime object
            same thing as `start_date` but as a datetime object
        `self.end_date_` : datetime object
            same thing as `start_date` but as a datetime object
        `self.web_scraping` : boolean
            decides to run or not the webscraping package in the `main.py` module
        `self.end_date_` : datetime object
            same thing as `start_date` but as a datetime object
        """

        # initialize value here
        self.start_date = "2021-08-06"
        self.end_date = "2021-08-10"
        self.tickers = ['FSR']
        self.db_name = 'financial_data.db'
        self.web_scrap_name = 'web_scrapping'
        self.start_date_ = datetime.strptime(self.start_date, "%Y-%m-%d")  # datetime object
        self.end_date_ = datetime.strptime(self.end_date, "%Y-%m-%d")  # datetime object
        self.web_scraping = True
        self.sentiment_analysis = True

        self.file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)),self.web_scrap_name, 'output',
                                          self.start_date + '_' + self.end_date)
        Path(self.file_name).mkdir(parents=True, exist_ok=True)  # create new path if it doesn't exist
        self.file_name = os.path.join(self.file_name, 'financial_data.db')
        self.delta_date = abs((self.end_date_ - self.start_date_).days)  # number of days between 2 dates

        #Headers for the FinnHub API
        self.news_header = ['category', 'datetime','headline','id','image','related','source','summary','url']

        try:
            self.start_date_ > self.end_date_
        except:
            print("'start_date' is after 'end_date'")

class InitStockTwit():
    """Class that initializes global value for the module sentiment analysis of Stock Twits
    """

    def __init__(self):
        """Built-in method to inialize the global values for the module sentiment analysis of Stock Twits

        Attributes
        ----------

        `self.columns_twits` : list
            List of name of the columns we store the information from twits
        `self.positive_level` : float
            Positive sentiment level at which we take a long position ona  stock
        `self.min_sample` : int
            Minimum

        """
        self.columns_twits = ['time_published', 'directional', 'text']
        self.positive_level = .6
        self.min_sample = 60

class InitReddit():
    """Class that initializes global value for the module sentiment analysis of Reddit
    """

    def __init__(self):
        """Built-in method to inialize the global values for the module sentiment analysis of Stock Twits

        Attributes
        ----------

        `self.columns_twits` : list
            List of name of the columns we store the information from twits
        `self.positive_level` : float
            Positive sentiment level at which we take a long position ona  stock
        `self.min_sample` : int
            Minimum

        """
        self.columns_twits = ['time_published', 'directional', 'text']
        self.positive_level = .6
        self.min_sample = 60