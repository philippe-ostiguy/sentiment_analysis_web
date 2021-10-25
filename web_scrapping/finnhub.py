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
from bs4 import BeautifulSoup
import html5lib
from datetime import datetime, timedelta,time
from dateutil.relativedelta import relativedelta
from decouple import config
import fasttext
import time
import sqlite3
from initialize import InitNewsHeadline
import re
import pandas as pd
import os
from pathlib import Path
import web_scrapping.package_methods as pm


class FinnHub(InitNewsHeadline):
    """Class to make API calls to FinnHub"""

    def __init__(self):
        """ Class constructor. Initialize newly created object

        Attributes
        ----------
        `self.max_call` : int
            maximum api calls per minute for the finhub API
        `self.time_sleep` : int
            seconds to sleep before making a new API call. Default is 60 seconds as the maximum number of API calls is
            per minute
        `self.finhub_key` : str
            finhub unique API key. Get yours here : https://finnhub.io/
        `PRETRAINED_MODEL_PATH` : str
            pre-trained model from the fasttext package. It's important to download the model ('lid.176.bin' or
             'lif.176.ftz' : https://amitness.com/2019/07/identify-text-language-python/) in the project's directory
            (or specify the path where it's downloaded in the variable)
        `self.model` : fct
            method in the package `fasttext` to  detect language.
        """

        super().__init__()

        #Initialize attributes values here
        self.max_call = 60
        self.time_sleep = 60
        self.finhub_key = config('FINHUB_KEY')
        PRETRAINED_MODEL_PATH = 'lid.176.bin'
        self.model = fasttext.load_model(PRETRAINED_MODEL_PATH)

        #Start date must be within 1 year from now for request with the free version of FinHub
        if (datetime.strptime(self.start_date, "%Y-%m-%d") <= (datetime.now() - relativedelta(years=1))):
            raise Exception("'start_date' is older than 1 year. It doesn't work with the free version of FinHub")

    def __call__(self,ticker, ticker_db):
        """Special function call operator to call the class object

       Parameters
        ----------

        `ticker` : str
            name of the current ticker as written in the Stock Exchange
        `ticker_db` : str
            name of the current ticker with a trailing underscore in the database. To avoid error with ticker like
            All State (ALL)
        `self.nb_request` : int
            nb of request made so far. Set to 0 in constructor `__init__` as we may loop through ticker
            and want to avoid the variable to reset to 0 when exiting the wrapper `iterate_day()` (which could generate
            an error)

        """

        self.nb_request = 0
        self.ticker = ticker
        self.ticker_db = ticker_db #different value because ticker like 'ALL' (All State) can generate
                                            # error in SQLite database
        self.js_data = []

        #call the methods here
        self.js_data.clear()
        self.req_new()
        self.create_table()
        self.clean_table()
        self.lang_review()


    def init_sql(func):
        """ Decorator that open the sql database, save it and close it. The operation are between the opening and
        saving of the file"""

        def wrapper_(self):
            conn_ = sqlite3.connect(self.file_name)
            c = conn_.cursor()
            func(self,conn_,c)
            conn_.commit()
            conn_.close()
        return wrapper_

    @init_sql
    def clean_table(self,conn_,c):
        """Method that clean the database using sqlite3

        Parameters
        ----------
        `conn_` : database object
            Connection object that represents the database
        `c` : database object
            Cursor object
        """

        #remove NULL entry (row) from headline column
        c.execute(f" DELETE FROM {self.ticker_db} WHERE {self.news_header[2]} IS NULL OR "
                  f"trim({self.news_header[2]}) = '';")
        # remove NULL value from datetime
        c.execute(f" DELETE FROM {self.ticker_db} WHERE {self.news_header[1]} IS NULL OR "
                  f"trim({self.news_header[1]}) = '';")

        #removes duplicate entries (row)
        c.execute(f" DELETE FROM {self.ticker_db} WHERE rowid NOT IN (select MIN(rowid)"
                  f"FROM {self.ticker_db} GROUP BY {self.news_header[2]})")

        #Remove hastags, url, users mentions ans whitespace using `re` package (regex)
        c.execute(f" SELECT {self.news_header[2]} FROM {self.ticker_db}")
        rows = c.fetchall()

        for item_ in rows:
            new_value = item_[0]
            #remove url
            new_value = re.sub("https?:\/\/.*[\r\n]*", "", new_value)

            #remove hastags
            new_value = re.sub("#", "", new_value)

            #remove mentions (@)
            new_value = re.sub("@\S+", "", new_value)

            #remove duplicated whitespaces
            new_value.replace("  "," ")

            #replace values
            query = f"UPDATE {self.ticker_db} SET {self.news_header[2]} = (?) WHERE {self.news_header[2]} = (?)"

            #query = f"Insert into {self.ticker_db} ({self.news_header[2]}) VALUES(\"%s\")" % (new_value)
            c.execute(query,(new_value,item_[0]))

    @init_sql
    def create_table(self,conn_,c):
        """ Method that creates a table in SQLite database. It creates the table  in `self.file_name` and write
        the data in it

        Parameters
        ----------
        `conn_` : database object
            Connection object that represents the database
        `c` : database object
            Cursor object
        """

        #create table if it does not exist
        c.execute(f'drop table if exists {self.ticker_db}')
        conn_.commit()
        c.execute(f"CREATE TABLE IF NOT EXISTS {self.ticker_db} ({self.news_header[0]})")
        conn_.commit()

        #add columns to the table if the columns don't exist
        for header_ in range(len(self.news_header)-1):
            c.execute(f"alter table {self.ticker_db} add column '%s' " % self.news_header[header_+1])
            conn_.commit()

        iteration = 0
        for data_ in self.js_data:
            iteration +=1
            try :
                c.execute(f'insert into {self.ticker_db} values (?,?,?,?,?,?,?,?,?)',[data_[self.news_header[0]],
                          data_[self.news_header[1]],data_[self.news_header[2]],data_[self.news_header[3]],
                        data_[self.news_header[4]],data_[self.news_header[5]],data_[self.news_header[6]],
                          data_[self.news_header[7]],data_[self.news_header[8]]])
            except:
                print(f"Error at the {iteration}th ieration")

            conn_.commit()

    def iterate_day(func):
        """ Decorator that makes the API call on FinHub each days between the `self.start_date`
        and `self.end_date` """

        def wrapper_(self):
            delta_date_ = pm.delta_date(self.start_date,self.end_date)
            date_ = self.start_date
            date_obj = self.start_date_

            for item in range(delta_date_ + 1):
                self.nb_request +=1
                func(self,date_)
                date_obj = date_obj + relativedelta(days=1)
                date_  = date_obj.strftime("%Y-%m-%d")
                if self.nb_request == (self.max_call-1):
                    time.sleep(self.time_sleep)
                    self.nb_request=0
        return wrapper_

    @init_sql
    def lang_review(self,conn_,c):
        """ Methods that delete non-english entries based on the 'headline' column in a SQLlite3 db based on `fasttext`
        package and `langdetect` package

        Parameters
        ----------
        `conn_` : database object
            Connection object that represents the database
        `c` : database object
            Cursor object
        """

        list_ = []
        c.execute(f" SELECT {self.news_header[2]} FROM {self.ticker_db}")
        rows = c.fetchall()

        #check for non-english headlines using `fasttext`package
        for item_ in rows:
            lang_type_ = self.model.predict(item_[0])[0][0].replace('__label__','')
            if lang_type_ != 'en':
                list_.append(item_[0])
            #delete non-english entries (rows)
            query = f"DELETE FROM {self.ticker_db} where {self.news_header[2]} in ({','.join(['?']*len(list_))})"
            c.execute(query, list_)

    @iterate_day
    def req_new(self,date_):
        """ Method that makes news request(s) to the Finnhub API"""
        request_ =  'https://finnhub.io/api/v1/company-news?symbol=' + self.ticker + '&from=' + date_ + \
                    '&to=' + date_ + '&token=' + self.finhub_key
        response_ = requests.get(request_)
        self.js_data += response_.json()