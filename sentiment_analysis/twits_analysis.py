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

"""Module to perform sentiment analysis on twits

"""

from initialize import InitProject
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from transformers import pipeline
from collections import defaultdict
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np
from scipy.special import softmax
import csv
import urllib.request
import time


class TwitAnalysis():
    """Class that performs sentiment analysis (NLP) on 'twit-like' media (stocktwit, reddit, twitter)

    """
    def __init__(self,init):
        """
        Parameters
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project
        """
        #Attributes
        #----------
        #`self.dict_sentiment` : dict
         #   it's the pandas.DataFrame `self.pd_stock_sentiment` but in dictionary to loop faster



        self.sentiment_analyser = pipeline("sentiment-analysis")
        self.init = init #class that initialises global variables for the project (and in the darkness bind them...
                        #well, not really)
        #self.dict_sentiment = {}


    def __call__(self):
        """Built-in `__call__` method to initialize the model"""
        self.init_roberta()

    def init_roberta(self):
        """Initialize Twitter Roberta based transformer """
        task = 'sentiment'
        MODEL = f"cardiffnlp/twitter-roberta-base-{task}"

        tokenizer = AutoTokenizer.from_pretrained(MODEL)

        # download label mapping
        self.labels = []
        mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{task}/mapping.txt"
        with urllib.request.urlopen(mapping_link) as f:
            html = f.read().decode('utf-8').split("\n")
            csvreader = csv.reader(html, delimiter='\t')
        self.labels = [row[1] for row in csvreader if len(row) > 1]

        # PT
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL)
        self.model.save_pretrained(MODEL)
        self.tokenizer.save_pretrained(MODEL)

    """
    def loop_twits(func):
        Decorator that loops the twits/comment

        def wrapper_(self):
            self.dict_sentiment = self.init.pd_stock_sentiment.to_dict('list')
            
            #iterate only over the comments of the dictionnary
            for twit in [comment for key,comment in self.dict_sentiment.items() if 
                         key == self.init.columns_sentiment[0]]:
                
                func(self,twit)
            return self.init.pd_stock_sentiment
        return wrapper_
    """

    def roberta_analysis(self,twit):
        """
        Performs sentiment analysis using Twitter Roberta based transformer model to make predictions.

        Parameters
        ----------
        `twit` : pandas.DataFrame
            twit/reddit comment that contains the comment itself

        """

        # extract sentiment prediction if there is a text in the stocktwit
        if (twit[self.init.columns_sentiment[0]] != "") and (twit[self.init.columns_sentiment[0]]):
            encoded_input = self.tokenizer(twit[self.init.columns_sentiment[0]], return_tensors='pt')
            output = self.model(**encoded_input)
            scores = output[0][0].detach().numpy()
            scores = softmax(scores)
            ranking = np.argsort(scores)
            ranking = ranking[::-1]

            #calclulate the 'net' sentiment for the twit/comment. Ex : the result could be ['Positive' : 0.7,
            # 'Neutral' : 0.2, 'Negative' :0.1]. The 'net' sentiment would be 1*0.7 - 0.1 *1 = 0.6

            score =0
            for i in range(scores.shape[0]):
                label = labels[ranking[i]]
                if label == 'positive' :
                    score += scores[ranking[i]]
                if label == 'negative':
                    score -=scores[ranking[i]]

            self.probabilities.append(score)



    """
    To test to make sure it works
    def finbert_analysis(self,twit,key):

        finbert = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone', num_labels=3)
        tokenizer = BertTokenizer.from_pretrained('yiyanghkust/finbert-tone')


        if (twit[1] != "") and (twit[1]):

            inputs = tokenizer(twit[1], return_tensors="pt", padding=True)
            outputs = finbert(**inputs)[0]
            scores = outputs[0].detach().numpy()
            scores = softmax(scores)

            labels = {0: 'neutral', 1: 'positive', 2: 'negative'}
            for idx, sent in enumerate(twit[1]):
                print(sent, '----', labels[np.argmax(outputs.detach().numpy()[idx])])

    """