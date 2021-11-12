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

"""Module for sentiment analysis on tickers of our choice. By default, data comes from the Finnhub API, which means
that the analysis should be done on company listed on US Exchange. We must use the same directory path to get the data
 as we use in the`webscrap_headlines` project"""

import sentiment_analysis as sa
import web_scrapping as ws
import matplotlib.pyplot as plt
import pandas as pd
from initialize import InitProject
from datetime import datetime, timedelta, time, date

class InitMain(InitProject):
    """Class that initializes global value for the project and performs some checks and stops the program if necessary
     """

    def __init__(self):
        """Built-in method to inialize the global values for the module
        """

        #get attributes from `initialize.py` module (global attributes for the package)
        super().__init__()

        #initialize value here
        self.us_holidays = []

    def __call__(self):
        # initialize the project variables
        init = InitProject()
        init()
        self.driver = init.driver
        self.time_ago = init.time_ago
        self.us_holidays = init.us_holidays
        self.check_closed_days()

    def check_closed_days(self):
        """ Function that checks if the current days is weekend or a US Stock holiday"""

        #check if current day is a holiday
        if ((datetime.now().month in [date_.month for date_ in self.us_holidays]) and
            (datetime.now().year in [date_.year for date_ in self.us_holidays]) and
            (datetime.now().day in [date_.day for date_ in self.us_holidays])):
            raise Exception("Current day is a US Stock holiday. The market is closed. The program will shut down")

        if (datetime.today().weekday()  >= 5):
            raise Exception("Current day is the weekend. The market is closed. The program will shut down")

if __name__ == '__main__':
    init_main = InitMain()
    init_main()

    #initialize the Roberta sentiment analysis
    init_roberta = sa.TwitAnalysis(init_main)
    init_roberta() #built-in call method to initialize the model

    # fetching the data on social media and twitter
    #ra_ = ws.RedditApi_(init_main,init_roberta)
    #init_main.pd_stock_sentiment= ra_() # return the comments with sentiment analysis using Twitter-based Roberta
    # Transformer

    #sta_ = ws.StockTwitsApi(init_main,init_roberta)
    #init_main.pd_stock_sentiment =  sta_()
    ta = ws.TwitsApi(init_main,init_roberta)
    init_main.pd_stock_sentiment = ta()
    t = 5


    #init.tickers = pp.get_tickers() #get_tickers() is to get tickers from all the companies listedin the s&p 500

    """
    Code for sentiment analysis using VaderAnalysis
    
    #built-in method `__call__` in `VaderAnalysis()` class
    init.pd_data = va(ticker_db=ticker_db,hist_price=init.pd_data)

    #Plotting the daily return against the sentiment score
    init.pd_data.plot(x =sentiment_name,y=daily_return,style = "o")

    #correlation between sentiment score and daily return
    print(init.pd_data[daily_return].corr(init.pd_data[sentiment_name]))

    #frequency histogram for the sentiment score
    plt.rcParams.update({'figure.figsize': (7, 5), 'figure.dpi': 100})
    x= init.pd_data[sentiment_name]
    plt.hist(x, bins=50)
    plt.gca().set(title='Frequency Histogram', ylabel='Frequency');
    """