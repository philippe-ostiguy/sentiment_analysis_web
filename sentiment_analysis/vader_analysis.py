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


import sqlite3
from os.path import isfile
import nltk
#from nltk.sentiment.vader import SentimentIntensityAnalyzer as sia
#nltk.download('vader_lexicon')
from datetime import datetime
from dateutil.relativedelta import relativedelta
from statistics import mean
from initialize import Init

class VaderAnalysis(Init):
    """Class that performs sentiment analysis (NLP) on financial news headlines using the VADER analyzer

    It's for sentiment analysis on tickers of our choice. By default, data comes from the Finnhub API, which means
    that the analysis should be done on company listed on US Exchange. We must use the same directory path to get the
    data as in the`webscrap_headlines` project
    """
    def __init__(self):
        """
        Parameters
        ----------
        All parameters are defined in the constructor (`__init__`) in `initialize.py` module

        `hist_price` : pd Dataframe
            Historical price with returns that we get from the Alpha Vantage API

        Attributes
        ----------
        `self.min_sample` : int
            minimum of headlines for a given day to be considered for sentiment analysis. By default, 30.
        `self.sentiment_name` : str
            Name of the sentiment analysis score in the pd Dataframe
        """

        #get the attributes (global attributes) from the `initialize.py`
        super().__init__()
        self.sentiment_name = 'Sentiment Score'
        #Initialize attributes here
        self.min_sample = 15

    def __call__(self,ticker_db,hist_price):
        """Special function call operator to call the class object callable

       Parameters
        ----------

        """

        self.ticker_db = ticker_db   #different value because ticker like 'ALL' (All State) can
                                                # generate error in SQLite database. We added a '_' to differentiate
        self.pd_data = hist_price
        self.start_debut_tempo = None #temporary datetime value (starting date)
        self.end_date_tempo = None #temporary datetime value (ending date)

        #executing the `self.vader_analysis()` function
        _ = self.vader_analysis()

        if not (self.sentiment_name in self.pd_data.columns):
            raise Exception(f"Column {self.sentiment_name} does not exist. That's probably because there was no days"
                            f"with a minimum sample `self.min_sample` of {self.min_sample}")
        else:
            return self.pd_data

    def check_size(self,conn_,c,date_, delta_day,index):
        """Method that checks every day if there are enough headlines `self.min_sample` to consider this day in the
        sentiment analysis

        For trading on Monday, it takes the news from Friday 9:30 am to Monday 9:29 am
        """

        date_ = date_.replace(hour = 9, minute = 30)
        self.start_debut_tempo = date_.timestamp() #convert to timestamp
        self.end_date_tempo  = self.start_debut_tempo + (24*60*60*delta_day)
        c.execute(f"SELECT count() from {self.ticker_db} where {self.news_header[1]} >= {self.start_debut_tempo} and "
                  f"{self.news_header[1]} < {self.end_date_tempo }")

        nb_of_data = c.fetchone()[0]
        if nb_of_data >= self.min_sample:
            return True
        else:
            return False

    def iterate_day(func):
        """ Decorator that performs the sentiment analysis on the news headlines between the `self.start_date`
        and `self.end_date` """

        def wrapper_(self,conn_,c):
            # not doing sentiment analysis for the last day, no return for the next day
            for index in range(len(self.pd_data)-1):
                delta_day = (self.pd_data.iloc[index+1,0] - self.pd_data.iloc[index,0]).days
                data_ = func(self,conn_,c,self.pd_data.iloc[index,0], delta_day,index)
            return data_
        return wrapper_

    def init_sql(func):
        """ Decorator that open the sql database, save it and close it. The operation are between the opening and
        saving of the file"""

        def wrapper_(self):
            if not isfile(self.file_name):
                raise Exception(f"Database {self.db_name}.db doesn't exist")
            conn_ = sqlite3.connect(self.file_name)
            c = conn_.cursor()
            data_ = func(self, conn_, c)
            conn_.commit()
            conn_.close()
            return data_
        return wrapper_

    @init_sql
    @iterate_day
    def vader_analysis(self, conn_, c,date_, delta_day,index):
        """Method that performs Sentiment analysis on news headlines. For a given day, the analysis is performed from
        9:30 am until 9:30 am (EST) the next day.

        For example, February 25th 2021 in the table would be analysis from news from 9:30am this morning until
        9:29 am February 26th 2021.
        """

        isValid= self.check_size(conn_,c,date_, delta_day,index)

        #if the sample is >= `self.min_sample`, performs sentiment analysis using Vader
        if isValid:
            list_results=[]
            c.execute(f"SELECT {self.news_header[2]}  from {self.ticker_db} where {self.news_header[1]} >= "
                      f"{self.start_debut_tempo} and {self.news_header[1]} < {self.end_date_tempo}")
            rows = c.fetchall()
            for row in rows:
                list_results.append(sia().polarity_scores(row[0])['compound'])

            #to make it easier, the sentiment score from previous day is on the same line than current day return
            #(index + 1 )
            self.pd_data.loc[index+1,self.sentiment_name] = mean(list_results)
        else:
            pass
        return self.pd_data