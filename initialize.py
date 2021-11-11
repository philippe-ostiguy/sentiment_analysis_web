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
import re
import requests
import bs4 as bs
import pandas as pd


def get_tickers():
    """Method that gets the stock symbols from companies listed in the S&P 500

    Return
    ------
    `tickers` : list
        S&P 500 company symbols
    """
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find_all('table')[0]  # Grab the first table

    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.strip('\n')
        tickers.append(ticker)

    return tickers


class InitProject():
    """Class in which we set and/or initialize the values of the variables (attribute) for the entire project"""

    def __init__(self):
        """Built-in method to set and inialize the global values for the project

        Attributes
        -----------
        `self.columns_sentiment` : list
            list of columns used in the pandas Dataframe (`self.pd_stock_sentiment`) in which
            we stored the sentiment analysis for each stock.
            Text is the text in the post, twit. Probability is the probility of the sentiment (-1 to +1. -1 with 100%
            chance of a negative sentiment and +1 with a 100% of a positive sentiment. Directional is applicable only
            for Stockwits (user can choose 'bullish' or 'bearish' when creating a twit).
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data.By default, the value is 24, and should not
            be changed. If it is changed, the funciton `self.set_time_ago()` should be reviewed. See module
            `reddit_api.py` for more info and search for the variable `self.time_ago`
        `self.us_holidars` : list
            List that contains the US Stock Holiday
        `self.pd_stock_sentiment` : pandas.DataFrame
            Pandas DataFrame that contains the sentiment/mood for each stock we are webscrapping on social media

        """

        #list of variables we can change ourself
        self.columns_sentiment = ['text','probability','directional']
        self.time_ago = 24

        # list of variables that we should not set ourself
        self.us_holidays = []
        self.pd_stock_sentiment = pd.DataFrame(columns=self.columns_sentiment)

    def __call__(self):

        # calling the functions
        self.get_us_holiday()


    def get_us_holiday(self):
        """Get the US Stock holidays """

        resp = requests.get('https://www.nyse.com/markets/hours-calendars')
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        # Grab the table with the US Stock holidays (first table)
        table = soup.find_all('table', {'class': 'table table-layout-fixed'})[0]
        if table == []:
            raise Exception("Table to get US stocks holiday in function `get_us_holiday()` does not exist")

        years_ = []

        # get the year in the header
        for headers_ in table.findAll('tr')[:1]:
            for header_ in headers_.findAll('th')[1:]:
                years_ += header_

        for holidays_ in table.findAll('tr')[1:]:

            i = 0
            for holiday_ in holidays_.findAll('td'):
                if "—" in holiday_.text:
                    i += 1
                    continue

                month_ = holiday_.text.split(' ')[1]
                day_ = re.sub("[^0-9]", "", holiday_.text.split(' ')[2])
                year_ = years_[i]
                date_ = "-".join([year_, month_, day_])
                self.us_holidays.append(datetime.strptime(date_, '%Y-%B-%d'))
                i += 1

        if not self.us_holidays :
            raise Exception(f"List ``self.us_holidays {self.us_holidays} is empty in package `initialize.py`")




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