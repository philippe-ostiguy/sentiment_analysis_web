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


class StockToTrade():
    """Class to decide which stock we webscrap data"""

    def __init__(self):
        """
        Attributes
        ----------
        `self.stocktwit_endpoint` : str
            Stockwit API's endpoint

        """

        self.stocktwit_endpoint = 'https://api.stocktwits.com/api/2/trending/symbols/equities.json'

    def get_trending(self):
        """Function to get the most trending stock on Stock Twits

        By default it will return the 30 most trending stocks
        """

        response = requests.get(self.stocktwit_endpoint)
        for stock in response.json()['symbols']:

            row = self.get_data(stock,self.response_parameters)
            self.trending_stocks = self.trending_stocks.append(row, ignore_index=True)


    def get_data(self,dict, keys_):
        """Function that stores the data from a dictionary with the specific keys in a a new dictionary
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
        return new_dict