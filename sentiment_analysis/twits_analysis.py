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

from initialize import InitStockTwit
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


class TwitAnalysis(InitStockTwit):
    """Class that performs sentiment analysis (NLP) on stocktwits

    """
    def __init__(self,stock_twits):
        """
        Parameters
        ----------
        `stock_twits` : pandas.DataFrame
            Stock twits with the time the post was published, the directional and the twit (opinion)

        Attributes
        ----------
        `self.twit_result` : pandas.DataFrame
            Probability and sentiment from the stocktwits
        `self.twit_columns` : list
            name of the column in the `self.twit_result` dataframe
        `self.models_to_test` : list
            all the transformers models we want to test

        """
        super().__init__()

        self.sentiment_analyser = pipeline("sentiment-analysis")
        self.twits = stock_twits
        self.twit_result = pd.DataFrame()
        self.twit_columns = ['probability','sentiment','directional', 'text']

        self.probabilities = [] #probability to be negative or positive
        self.sentiments = [] #sentiment of the tweet (negative, positive, neutral)
        self.directional = [] #directional returned by stocktwits (bullish or bearish)
        self.text_ = [] #stocktwit (text)

        self.accuracy = 0 #accuracy of the predictive model
        self.total = 0 #total of value used to calcuate `self.accuracy`
        self.mean_ = 0 #mean of the `self.probabilities`

    def __call__(self):
        """Built-in `__call__` method that loops through the twits to predict sentiment mood."""

        for twit in self.twits.values:

            self.roberta_analysis(twit)

        # add probability and sentiment predictions to tweet dataframe
        self.twit_result[self.twit_columns[0]] = self.probabilities
        self.twit_result[self.twit_columns[1]] = self.sentiments
        self.twit_result[self.twit_columns[2]] = self.directional
        self.twit_result[self.twit_columns[3]] = self.text_

        if self.total!= 0:
            self.accuracy = self.accuracy/ self.total
        self.mean_ = self.twit_result[self.twit_columns[0]].mean()

        return self.twit_result, self.accuracy,self.mean_

    def append_results(self,twit,label):
        """Method that appends the sentiment, directional and calclulate the accuracy of the prediction

        Parameters
        ----------
        `twit` : pandas.DataFrame
            Stock twit with the time the post was published, the directional and the twit (opinion)
        `label` : str
            sentiment of the twit labeled by the transformer (negative or positive)
        """

        if (twit[0] == 'Bullish'):
            self.directional.append('POSITIVE')
            self.total += 1
            if (label == 'POSITIVE'):
                self.accuracy+=1
        elif (twit[0] == 'Bearish'):
            self.directional.append('NEGATIVE')
            self.total += 1
            if (label == 'NEGATIVE'):
                self.accuracy += 1
        else:
            self.directional.append('NEUTRAL')

    def roberta_analysis(self,twit):
        """
        Performs sentiment analysis using Twitter Roberta based transformer model to make predictions.

        Parameters
        ----------
        `twit` : pandas.DataFrame
            Stock twit with the time the post was published, the directional and the twit (opinion)
        """

        task = 'sentiment'
        MODEL = f"cardiffnlp/twitter-roberta-base-{task}"

        tokenizer = AutoTokenizer.from_pretrained(MODEL)

        # download label mapping
        labels = []
        mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{task}/mapping.txt"
        with urllib.request.urlopen(mapping_link) as f:
            html = f.read().decode('utf-8').split("\n")
            csvreader = csv.reader(html, delimiter='\t')
        labels = [row[1] for row in csvreader if len(row) > 1]

        # PT
        model = AutoModelForSequenceClassification.from_pretrained(MODEL)
        model.save_pretrained(MODEL)
        tokenizer.save_pretrained(MODEL)

        # extract sentiment prediction if there is a text in the stocktwit
        if (twit[1] != "") and (twit[1]):
            encoded_input = tokenizer(twit[1], return_tensors='pt')
            output = model(**encoded_input)
            scores = output[0][0].detach().numpy()
            scores = softmax(scores)
            ranking = np.argsort(scores)
            ranking = ranking[::-1]

            score =0
            for i in range(scores.shape[0]):
                label = labels[ranking[i]]
                if label == 'positive' :
                    score += scores[ranking[i]]
                if label == 'negative':
                    score -=scores[ranking[i]]

            if score >= 0 :
                label = 'POSITIVE'
            else:
                label = 'NEGATIVE'

            self.sentiments.append(label) # 'POSITIVE' or 'NEGATIVE'
            self.probabilities.append(score)
            self.text_.append(twit[1])
            self.append_results(twit,label)


        def distilbert_analysis(self,twit,key):
            """ Performs sentiment analysis using flair DistilBERT transformer model to make predictions."""

            result = self.sentiment_analyser(twit[1])[0]

            self.sentiments[key].append(result['label'])  # 'POSITIVE' or 'NEGATIVE'
            # extract sentiment prediction
            if (twit[1] != "") and (twit[1]):
                if (result['label'] == 'NEGATIVE'):
                    self.probabilities[key].append(-result['score']) #numerical score is negative as sentiment is negative
                else :
                    self.probabilities[key].append(result['score']) #numerical score is positive as sentiment is negative

            self.append_result(twit,key,result['label'])

            self.sentiments[key].append(result['label'])  # 'POSITIVE' or 'NEGATIVE'
            if (twit[0] == 'Bullish'):
                self.directional[key].append('POSITIVE')
                self.total[key] += 1
                if (result['label'] == 'POSITIVE'):
                    self.accuracy[key] += 1
            elif (twit[0] == 'Bearish'):
                self.directional[key].append('NEGATIVE')
                self.total[key] += 1
                if (result['label'] == 'NEGATIVE'):
                    self.accuracy[key] += 1
            else:
                self.directional[key].append('NEUTRAL')


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