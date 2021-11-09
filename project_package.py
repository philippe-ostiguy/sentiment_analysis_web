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

"""Module with functions that are useful for the project. The functions can be used for the whole project."""

import requests
import bs4 as bs
from datetime import datetime
import re

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

class ProjectVariables:
    """Variables that are used across the project. We want to initialize them only once"""


    def __init__(self):
        """
        `self.us_holidays` : list
            list of datetime object when the us stock market is closed (NYSE)
        """
        self.us_holidays = []

    def __call__(self):

        #calling the functions
        self.get_us_holiday()

    def get_us_holiday(self):
        """Get the US Stock holidays """

        resp = requests.get('https://www.nyse.com/markets/hours-calendars')
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        # Grab the table with the US Stock holidays (first table)
        table = soup.find_all('table', { 'class' : 'table table-layout-fixed' })[0]
        if table == []:
            raise Exception("Table to get US stocks holiday in function `get_us_holiday()` does not exist")

        years_ = []

        #get the year in the header
        for headers_ in table.findAll('tr')[:1]:
            for header_ in headers_.findAll('th')[1:]:
                    years_ += header_

        for holidays_ in table.findAll('tr')[1:]:

            i = 0
            for holiday_ in holidays_.findAll('td'):
                if "—" in holiday_.text :
                    i+=1
                    continue

                month_ = holiday_.text.split(' ')[1]
                day_ = re.sub("[^0-9]", "", holiday_.text.split(' ')[2])
                year_ = years_[i]
                date_ = "-".join([year_,month_,day_])
                self.us_holidays.append(datetime.strptime(date_,'%Y-%B-%d'))
                i+=1
