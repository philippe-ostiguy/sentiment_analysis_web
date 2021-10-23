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
from initialize import InitNewsHeadline, InitStockTwit
import requests
import bs4 as bs
from transformers import BertTokenizer, BertForSequenceClassification
from scipy.special import softmax
import numpy as np

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

class InitMain(InitNewsHeadline,InitStockTwit):
    """Class that initializes global value for the project. It also use general method to initialize value.
     """

    def __init__(self):
        """Built-in method to inialize the global values for the module
        """

        #get attributes from `initialize.py` module (global attributes for the package)
        super().__init__()

        #initialize value here
        self.pd_data = pd.DataFrame()

        ra_ = ws.RedditApi_()
        ra_() #call the built-on method 'call'
        sta_ = ws.StockTwitsApi()
        sta_()
        ba = sa.TwitAnalysis(sta_.stock_twit)
        ba()

if __name__ == '__main__':
    init = InitMain()
    #init.tickers = get_tickers() #get_tickers() is to get tickers from all the companies listedin the s&p 500

    #if we want to perform a news headline web_scraping using FinnHub
    if init.web_scraping:
        ta_ = ws.TwitterApi_()
        ta_() #call the built-on method 'call'
        #fh_ = ws.FinnHub()

    # if we want to perform a news headline web_scraping using FinnHub
    if init.sentiment_analysis:


        hr = ws.HistoricalReturn()
        daily_return = hr.daily_return
        #va = sa.VaderAnalysis()
        #sentiment_name=va.sentiment_name
        t = 5

    for ticker in init.tickers:
        ticker_db = ticker + '_'

        if init.web_scraping:
            #fh_(ticker, ticker_db)
            pass

        if init.sentiment_analysis:
            init.pd_data = hr(ticker=ticker)


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