#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-
###############################################################################
#
#  The MIT License (MIT)
#  Copyright (c) 2021 Philippe Ostiguy
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to de al
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
import perform_stats as ps
import stock_to_trade as stt
import time
import sys
import os
from twilio.rest import Client
import logging
import csv

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
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.driver_parameters = init.driver_parameters
        self.time_ago = init.time_ago
        self.us_holidays = init.us_holidays
        self.pd_metrics = init.pd_metrics
        self.pd_timer = init.pd_timer
        self.check_closed_days()

    def check_closed_days(self):
        """ Function that checks if the current days is weekend or a US Stock holiday"""

        #check if current day is a holiday

        for date_ in self.us_holidays:
            if ((datetime.now().month == date_.month) and (datetime.now().year == date_.year) and
                    (datetime.now().day == date_.day)):
                raise Exception("Current day is a US Stock holiday. The market is closed. The program will shut down")

        #if (datetime.today().weekday()  >= 5):
         #   raise Exception("Current day is the weekend. The market is closed. The program will shut down")

if __name__ == '__main__':

    init = InitMain()
    init()

    # logging error in a log file
    logging.basicConfig(filename=init.logger_file, level=logging.ERROR)
    # checking if there is an error and log it into the log file

    try:
        #decide which stock we webscrap
        stt_ = stt.StockToTrade(init)
        stt_()

        #initialize the Roberta sentiment analysis
        init_roberta = sa.TwitAnalysis(init)
        init_roberta() #built-in call method to initialize the model

        #initialize all classes we want to webscrap data
        ra_ = ws.RedditApi_(init, init_roberta) # Reddit
        sta_ = ws.StockTwitsApi(init, init_roberta) # Stocktwits
        sta_()
        ta = ws.TwitsApi(init, init_roberta) # Twitter
        ta()

        #initialize the class to calculate the metrics
        cm = ps.CalculateMetrics(init)

        #webscrapping data for reddit only one time (all comments for the different stocks are on the same posts)
        ra_.webscrap()

        for stock,keywords in init.stock_dictionnary.items():
            init.current_stock = stock #changing to current stock in loop
            init.pd_stock_sentiment.drop(init.pd_stock_sentiment.index, inplace=True) #drop values in the pandas Dataframe
            # fetching the data on social media and twitter

            # return the comments with sentiment analysis using Twitter-based Roberta Transformer on reddit, twitter,
            #stocktwits

            init.pd_stock_sentiment = ra_.write_values()
            init.pd_stock_sentiment =  sta_.webscrap()
            init.pd_stock_sentiment = ta.webscrap()

            #calculate the metrics
            init = cm()

        #decide the stock we take a position (or keep/exit)
        #dp_ = stt.DecidePosition(init)
        #dp_()

        #Wwriting the file with the resuts
        init.pd_metrics.to_csv(init.results_file,encoding='utf-8')
        #writing the time it took to run the program
        init.pd_timer.to_csv(init.timer_file,encoding='utf-8')

        os.system(f'say -v "Victoria" "The program is done. You can check it out."')

        #sending a SMS to say the program worked
        client = Client(init.twilio_sid, init.twilio_auth)
        message = client.messages \
            .create(
            body="The webscrapping worked",
            from_=init.from_phone,
            to=init.to_phone
        )

    except :
        os.system(f'say -v "Victoria" "The program crashed. Check it please"')
        logging.exception('Got exception on main handler')

        #sending a SMS to say the program did not work
        client = Client(init.twilio_sid, init.twilio_auth)
        message = client.messages \
            .create(
            body="The webscrapping did not work",
            from_=init.from_phone,
            to=init.to_phone
        )

        #print(e)

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