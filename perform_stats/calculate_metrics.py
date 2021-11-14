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

"""Module to calculate metrics with the results obtained (sentiment mood)
"""

import pandas as pd


class CalculateMetrics():

    def __init__(self,init):


        # We should touch these data. They come from the classes where we initialize the data
        self.init = init  # variable for the class containing the global variables for the project
        self.pd_subset = pd.DataFrame()

    def __call__(self):

        self.nb_comments()
        self.average_sentiment()
        self.total_comments()
        self.total_average_sentiment()
        return self.init

    def loop_source(func):
        """Decorator to loop throught the different sources where we webscrap the data"""

        def wrapper_(self):
            for source in self.init.comment_source:
                self.pd_subset = self.init.pd_stock_sentiment[self.init.pd_stock_sentiment
                                                              [self.init.columns_sentiment[3]]==source]
                func(self,source)
            return None
        return wrapper_

    @loop_source
    def nb_comments(self,source):
        """Number of twits/comments per source (reddit, twitter, stocktwits)"""

        self.init.pd_metrics.loc[list(self.init.current_stock.keys())[0],self.init.columns_metrics[3] + source] \
            = int(len(self.pd_subset.index))

    @loop_source
    def average_sentiment(self,source):
        """Average sentiment mood per source (reddit, twitter, stocktwits)"""
        self.init.pd_metrics.loc[list(self.init.current_stock.keys())[0], self.init.columns_metrics[2] + source] \
            = self.pd_subset[self.init.columns_sentiment[1]].mean()

    def total_comments(self):
        """return the total number of comments/twits for all the source"""
        self.init.pd_metrics.loc[list(self.init.current_stock.keys())[0], self.init.columns_metrics[1]] \
            = int(len(self.init.pd_stock_sentiment))

    def total_average_sentiment(self):
        """return the total average sentiment mood for all the source"""
        self.init.pd_metrics.loc[list(self.init.current_stock.keys())[0], self.init.columns_metrics[0]] \
            = self.init.pd_stock_sentiment[self.init.columns_sentiment[1]].mean()