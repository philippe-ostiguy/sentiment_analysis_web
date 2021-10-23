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

"""It's the module to get info and make API calls to StockTwits"""

import requests
from datetime import datetime, timedelta,time
import time
from initialize import InitStockTwit
import re
import pandas as pd
import web_scrapping.package_methods as pm
import os
import sentiment_analysis as sa
from selenium import webdriver
from collections import defaultdict
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class StockTwitsApi(InitStockTwit):
    """Class to make API Calls to the Stocktwits API

    No need to authenticate (but API rate limit is lower than if we authenticate). We use the class to get the most
    active stocks on Stock Twits (at the moment of writting that).
    """

    def __init__(self):
        """
        Attributes
        ----------
        `self.api_endpoint` : str
            API's endpoint parameter
        `self.most_active_endpoint` : str
            Most active endpoint we want to webscrap
        `self.response_parameters` : list
            list containing the parameters we want to get from the API response
        `self.driver_file_name` : str
            Chrome driver's file name
        `self.scroll_pause_time` : long
            pause time when scrolling down the page
        `self.class_time` : str
            Name of the class in Stocktwits containing the published time of a twit
        `self.class_twits` : str
            Name of the class in Stocktwits containing the twits (text, directional)
        `self.class_directional` : str
            Name of the class with the directional (bull or bear)
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. This value must be 1 hour or more as the time
            format in Stockwits is 'hh:mm AM (or PM)' except when it's under 1 hour.
        `self.ticker_st` : str
            Ticker we want to webscrap
        `self.stock_endpoint` : str
            Endpoint of the stock we want to webscrap

        """
        super().__init__()

        self.api_endpoint = 'https://api.stocktwits.com/api/2/trending/symbols/equities.json'
        self.most_active_endpoint = 'https://stocktwits.com/rankings/most-active'
        #self.ticker_st = 'SPY' #by the default we webscrap the SPY
        self.stock_endpoint = 'https://stocktwits.com/symbol/'
        self.tempo_endpoint = '' #Temporary endpoint - we add the ticker we want to webscrap at the end of
                                 #self.stock_endpoint
        self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chromedriver')
        self.response_parameters = ['symbol']
        self.scroll_pause_time = 2
        self.class_time = 'st_28bQfzV st_1E79qOs st_3TuKxmZ st_1VMMH6S' #time
        self.class_twits = 'st_29E11sZ st_jGV698i st_1GuPg4J st_qEtgVMo st_2uhTU4W'
        self.class_directional = 'lib_XwnOHoV lib_3UzYkI9 lib_lPsmyQd lib_2TK8fEo' #bull or bear
        self.time_ago = 1
        self.date_ = '' #date if different from today in the Xpath
        self.trending_stocks = pd.DataFrame() #trending stocks on stocktwits
        self.stock_twit = pd.DataFrame() #Twits on Stocktwits

    def __call__(self):

        self.convert_time()
        self.get_trending()

        self.twit_result  = pd.DataFrame()
        self.accuracy = defaultdict(list)
        self.mean_ = defaultdict(list)

        #for all the trending stocks in stocktwits, we get the 'twit results' (sentiment mood, probability and
        #directional - bull or bear), the prediction accuracy and the mood prediction
        for stock in self.trending_stocks['symbol']:
            self.tempo_endpoint = self.stock_endpoint + stock
            self.webscrap_content()
            ba = sa.TwitAnalysis(self.stock_twit)  # initialize the `BertAnalysis` class
            self.twit_result, self.accuracy[stock],self.mean_[stock] = ba()
            del ba
            self.tempo_endpoint = ''
            self.twit_result = pd.DataFrame()
        t = 5

    def get_trending(self):
        """Function to get the most trending stock on Stock Twits

        By default it will return the 30 most trending stocks
        """

        response = requests.get(self.api_endpoint)
        for stock in response.json()['symbols']:

            row = pm.get_data(stock,self.response_parameters)
            self.trending_stocks = self.trending_stocks.append(row, ignore_index=True)

    def convert_time(self):
        """Method to convert time readable in the Xpath in Selenium. Things to know :
        """

        now = datetime.now()  # get the current datetime, this is our starting point
        start_time = now - timedelta(hours=self.time_ago)  # datetime according to the number of the days ago we want
        #now = now.strftime(self.date_format)  # convert now datetime to format for API

        #Write the day in Xpath format for stocktwits
        text = [str(start_time.month), str(start_time.day),start_time.strftime('%y')]
        self.date_ = ('/'.join(text))

    def webscrap_content(self):
        """Method to web-scrap content on Stocktwits
        """

        driver = webdriver.Chrome(executable_path=self.driver_file_name)
        driver.get(self.tempo_endpoint)
        time.sleep(2)

        twit_dictionary = {} #dictionary with information from twits

        self.scroll_to_end(driver)
        stock_twits = driver.find_elements_by_xpath(
            "//div[contains(@class,'{}')]".format(self.class_twits))

        for twit in stock_twits:
            # keep the text after the symbol which is the opinion expressed
            bullish = 'Bullish'
            bearish = 'Bearish'
            if bullish in twit.text or bearish in twit.text:
                twit_tempo = twit.text.split('\n', 3)[3:][0]

            else:
                twit_tempo = twit.text.split('\n', 2)[2:][0]

            #remove all unescessary text (emoji, \n, other symbol like $)
            twit_tempo = pm.text_cleanup(twit_tempo)

            twit_dictionary[self.columns_twits[2]] = twit_tempo

            twit_dictionary[self.columns_twits[1]] = '' #set directional to 'empty'
            directional = re.search('\n(.*)\n', twit.text) #searching for 'bearish' or 'bullish' in the twit
            #If 'Bullish' or 'bearish', set the column 'directional to 'bullish or 'bearish accordindly.
            if (directional.group(1) == 'Bearish' or directional.group(1) == 'Bullish'):
                twit_dictionary[self.columns_twits[1]] = directional.group(1)
                # set the value in the column 'time_published'
                twit_dictionary[self.columns_twits[0]] = "\n".join(twit.text.split("\n", 3)[2:3])
                t = 5

            #If the directional is not mentioned, then `directional.group(1)` is the 'time_published'
            else:
                twit_dictionary[self.columns_twits[0]] = directional.group(1)

            self.stock_twit = self.stock_twit.append(twit_dictionary,ignore_index=True)


    def scroll_to_end(self,driver):

        wait = WebDriverWait(driver, self.scroll_pause_time)
        element_ = None
        while not element_:

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                element_ = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class,'{}') "
                               "and contains(text(),'{}')]".format(self.class_time,self.date_))))

            except TimeoutException:
                pass

