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

"""Module to extract data from the Alpha Vantage's API. It cleans, stores and does calculation on the data
(stock return) """

from decouple import config
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
from initialize import InitNewsHeadline

class InitAV(InitNewsHeadline):
    """Class to initialize attributes that are specific to the Alpha Vantage API """

    def __init__(self):
        """
        Attributes
        ----------
        `self.av_key` : str
            Alpha Vantage unique API key. Get yours here : https://www.alphavantage.co//
        `self.output_size` : str
            Can be 'full' or 'compact'. 'full' will return all the data covering 20+ years of historical data whereas
            'compact' will return the latest 100 data points. Default to 'full' here to have enough data..
        """

        #get initialized variable from the `initialize.py module`
        super().__init__()

        # Initialize attributes values here
        self.av_key = config('AV_KEY')
        self.output_size = 'full'

class HistoricalReturn(InitAV):
    """Class to get daily historical price from Alpha Vantage, calculate daily return using """

    def __init__(self):
        """
        Attributes
        ----------
        `self.adj_close` : str
            Name for the adjusted close price column
        `self.daily_return` : str
            Name of the column daily return in the pd Dataframe
        """

        super().__init__()

        #initialize values here
        self.adj_close = 'Adjusted Close'
        self.daily_return = 'Daily Return'


    def __call__(self,ticker):
        """Special function call operator to call the class object

       Parameters
        ----------
        `ticker` : str
            name of the current ticker as written in the Stock Exchange

        """
        self.ticker = ticker
        self.pd_data = pd.DataFrame()
        return self.historical_price()

    def historical_price(self):
        """ Method that get the historical price from the Alpha Vantage API, store and manipulate in a pandas Dataframe
        """

        app = TimeSeries(key=self.av_key,output_format='pandas')
        self.pd_data, _ = app.get_daily_adjusted(self.ticker, outputsize=self.output_size)
        self.pd_data.index = pd.to_datetime(self.pd_data.index)

        #Cleaning - drop N/A
        self.pd_data = self.pd_data.dropna()

        #Keeping only requested date range
        self.pd_data = self.pd_data.loc[(self.pd_data.index >= self.start_date_) &
                                        (self.pd_data.index <= self.end_date_)]

        # Keeping only 'Adjusted Close' column
        self.pd_data = self.pd_data.iloc[:,[4]]
        self.pd_data.columns =  [self.adj_close]

        #reverse row order
        self.pd_data = self.pd_data.reindex(index = self.pd_data.index[::-1])

        # Calculate daily return
        self.pd_data[self.daily_return] = self.pd_data.div(self.pd_data.shift(1)) -1
        self.pd_data = self.pd_data.reset_index(inplace=False)
        return self.pd_data

    def get_return(self):
        """ Method to get the return between 2 dates"""
        app = TimeSeries(key=self.av_key,output_format='pandas')
        self.pd_data, _ = app.get_daily_adjusted(self.ticker, outputsize=self.output_size)
        self.pd_data.index = pd.to_datetime(self.pd_data.index)

        pass