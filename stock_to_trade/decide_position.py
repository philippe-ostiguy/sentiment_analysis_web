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

"""Module to determine the stock that we take or close a position (long, short)"""

class DecidePosition():
    """Class to decide which stock we take a position or exist"""

    def __init__(self,init):
        """
        Attributes
        ----------
        `self.nb_trending` : int
            nb of trennding stocks we want to webscrap from stocktwits

        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project
        """

        self.init = init


    def __call__(self):
        #if we already know some stock we want to webscrap data. Set in `self.stock_dictionary` in `initialise.py`
        for ticker in self.init.stock_dictionnary:
            self.adjust_keywords(ticker,self.init.stock_dictionnary[ticker])
        self.get_trending()
        self.shorted_finviz()
        self.check_position()
        self.check_cap()
        t=5

    def decide_position(self):
        """Method to decide if we take a short or long position on a stock"""
