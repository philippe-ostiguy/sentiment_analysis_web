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
        self.dict_ = {} #we put temporarily the results (mood, tedt) from `self.pd_stock_sentiment` in this dictionary
                        #to make manipulations faster (manipulations on dictionaries are faster than on pandas
                        # Dataframe)
        self.pd_subset

    def __call__(self):
        students = [('jack', 'Apples', 34),
                    ('Riti', 'Mangos', 31),
                    ('Aadi', 'Grapes', 30),
                    ('Sonia', 'Apples', 32),
                    ('Lucy', 'Mangos', 33),
                    ('Mike', 'Apples', 35)
                    ]
        # Create a DataFrame object
        self.dfObj = pd.DataFrame(students, columns=['Name', 'Product', 'Sale'])

        self.pd_to_dict()

        return self.init

    def pd_to_dict(self):
        t = 5

    def nb_comments(self):
        self.pd_subset = self.dfObj[self.dfObj['Product'] == 'Apples']
        self.lenght = len(self.pd_subset.index)
        self.mean = self.pd_subset['Sale'].mean()
        t  = 5




        """
        self.columns_sentiment = ['text','probability','directional','source']
        self.columns_metrics = ["Sentiment average for ","Total sentiment average", "Nb of comments for ",
                                "Total number of comments", "Stocktwits sentiment accuracy"]
        self.comment_source = ['reddit','stocktwit','twitter']
        self.time_ago = 24
        self.pause_time = 2

        # list of variables that we should not set ourself
        self.us_holidays = []
        self.stock_dictionnary = {'Tsla': ['TSLA', 'Tesla', 'tesla']} #this will be changed later and set
                                                                            #automatically
        self.pd_stock_sentiment = pd.DataFrame(columns=self.columns_sentiment)
        """

