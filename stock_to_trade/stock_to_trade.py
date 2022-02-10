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
##############################################################################

"""Module to determine the stock we want to webscrap the data from"""

import requests
import string
import bs4 as bs

class StockToTrade():
    """Class to decide which stock we webscrap data"""

    def __init__(self,init):
        """
        Attributes
        ----------
        `self.stocktwit_trending` : str
            Stockwit API's endpoint to get the trending stocks
        `self.nb_trending` : int
            nb of trennding stocks we want to webscrap from stocktwits

        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project
        """

        self.nb_trending = 10
        self.stocktwit_trending = 'https://api.stocktwits.com/api/2/trending/symbols/equities.json'
        self.init = init


    def __call__(self):
        #self.get_trending()
        self.shorted_finviz()
        self.check_position()
        self.check_cap()
        t=5

    def set_trending(self,stock,is_trending):
        """ We set in the dict `self.trending_stock` if the stock is a trending stock `True` or not `False`
        on stocktwits. If it is a trending stock, then we will retrieve comments less further ago (using
        `self.time_ago_trend` vs `self.time_ago_no_trend`"""

        #make sure the stock doesn't exist in the dictionary yet
        if not stock in self.init.trending_stock.keys():
            self.init.trending_stock[stock] = is_trending

    def check_position(self):
        """"""
        pass

    def check_cap(self):
        """make sure the stocks has the minimum desired market cap. If not it is remove form the stock we want
        to webscrap"""

        tempo_dict = self.init.stock_dictionnary.copy()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',  # Do Not Track Request Header
            'Connection': 'close'
        }

        for ticker in self.init.stock_dictionnary:
            url = ''.join(['https://finance.yahoo.com/quote/', ticker, '/key-statistics?p=',ticker])
            response = requests.get(url,headers=headers)

            #check if we have a redirect
            is_redirect = False
            for response_ in response.history:
                if response_.status_code == 302:
                    tempo_dict.pop(ticker, None)
                    is_redirect = True
                    break

            if is_redirect:
                continue

            soup = bs.BeautifulSoup(response.text, 'lxml')
            # Grab the table with the market cap in it
            table = soup.find_all('table', {'class': 'W(100%) Bdcl(c)'})[0]
            if table == []:
                raise Exception("Table to get US market cap in function `check_cap()` does not exist")

            # get the market capitalisation only
            for row_ in table.findAll('tr')[0:1]:
                for market_cap_ in row_.findAll('td')[1:2]:
                    market_cap = market_cap_.text

            if market_cap == 'N/A':
                tempo_dict.pop(ticker, None)
                continue

            #check if market cap is in 'Trillions' (T),'Billions' (B) or 'Millions' (M)
            elif "T" in market_cap:
                market_cap = 10**12*float(market_cap.replace('T',''))
            elif 'B' in market_cap:
                market_cap = 10**9*float(market_cap.replace('B',''))
            elif 'M' in market_cap:
                market_cap = 10**6*float(market_cap.replace('M',''))
            else:
                tempo_dict.pop(ticker, None)
                continue

            if market_cap < self.init.min_cap:
                tempo_dict.pop(ticker, None)

        self.init.stock_dictionnary = tempo_dict

    def get_trending(self):
        """Function to get the most trending stock on Stock Twits
        By default it will return the 30 most trending stocks
        """

        response = requests.get(self.stocktwit_trending)
        i =0
        symbol_list = response.json()['symbols']
        for stock in symbol_list:
            symbol = self.get_data(stock,['symbol'])
            stock_name =  self.get_data(stock,['title'])
            #make sure the ticker doesn't already in our list of stocks we want to webscrap before adding it to the list
            if not symbol in self.init.stock_dictionnary:
                symbol = self.adjust_keywords(symbol,stock_name)

            #we reached the nb of trending stocks we wanted
            i+=1

            self.set_trending(symbol, True)
            if i == self.nb_trending:
                break

    def call_bs(self,url, element, class_str ):
        """Method to call beautiful soup and retun table(s)

        Parameters
        ---------
        `url` : str
            url where we webscrap data
        `element` : str
            html element where we want to get data
        `class_str` : str
            class of the html element
        """

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        resp = requests.get(url, headers=headers)
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        return soup.find_all('tr', {'valign': class_str})


    def shorted_finviz(self):
        """Method to get the most shorted stock on finviz. See begginning of this module
        to understand the parameters used in this method"""

        accepted_values = [0,5,10,15,20,25,30]
        if not self.init.short_level in accepted_values:
            raise Exception(f"Parameter `self.init.short_level` most be {accepted_values}. Current value is "
                            f"{self.init.short_level}. This is because the free version of Finviz only accepts these "
                            f"values.")


        symbol_list = []
        symbol_exist = False
        ticker_number = 1 #which page we are. On finviz, for the shorted stocks, it displays 20 ticker per page.
                        #So the first page will look like : https://finviz.com/screener.ashx?v=111&f=sh_short_o25&r=1,
                        #the second : https://finviz.com/screener.ashx?v=111&f=sh_short_o25&r=21, etc.

        while not symbol_exist:
            url_ = ''.join(['https://finviz.com/screener.ashx?v=111&f=sh_short_o', str(self.init.short_level),'&r=',
                            str(ticker_number)])

            tables = []
            tables = self.call_bs(url_, 'tr', 'top')

            for table in tables[1:]:
               #getting the ticker
                for row in table.findAll('td')[1:2]:
                    # we check if we already have the symbol in the list. It will tell us that we are at the end
                    # of the list in finviz
                    if row.text in symbol_list:
                        symbol_exist = True
                        break
                    symbol_list.append(row.text)
                    ticker = row.text

                #getting the company name
                for row in table.findAll('td')[2:3]:
                    company = row.text

                #symbol already exist, we are at the end of the list in Finviz
                if symbol_exist:
                    break

                ticker = self.adjust_keywords(ticker, company)
                self.set_trending(ticker, False)

            #go to the next page
            ticker_number +=20


    def adjust_keywords(self,symbol,stock_name):
        """Method that adjust the keyword for the stock we are searching on Reddit so that they can be found easily.
        It returns the new dictionary with adjusted keywords. The list of keywords we will be looking for a stock will
        be the ticker in capitalized letter only. We could also add the name of the company in lower case and the
        name of the company with the first letter in capitalized letter (they are commented below)

        Ex: For Apple, the keyword will be AAPL

        N.B. It's risky to search the ticker in lower case. Let's take the SPY, we will search for 'spy' which has
        a total different meaning"""

        new_keywords = []
        #remove 'undesired' word (inc, corp, etc.)
        for removing_ in self.init.keywords_to_remove:
            stock_name = stock_name.replace(removing_,'')

        # Remove single letter words (class A, etc.)
        stock_name = ' '.join([word for word in stock_name.split() if len(word) > 1])

        #Remove leading or trailing space
        stock_name = stock_name.strip()
        symbol = symbol.strip()

        # remove duplicated whitespaces
        stock_name = stock_name.replace("  ", " ")

        #all letter of symbol in cap letter
        new_keywords.append(symbol.upper())

        #stock with characters in lower case
        #new_keywords.append(stock_name.lower())

        #Stock and ticker with each first letter of each word in uppercase
        #new_keywords.append(string.capwords(stock_name.lower()))

        self.init.stock_dictionnary[symbol] = new_keywords
        return symbol

    def get_data(self,dict, keys_):
        """Function that stores the data from a dictionary with the specific keys in a new dictionary
        Parameters
        ----------
        `dict` : dictionary
            API's endpoint parameter
        `keys_` : list
            list of the keys in the dictionary we want to store in the new_didt
        """
        new_dict = {}
        for key in keys_:
            new_dict[key] = dict[key]
        return new_dict[key]