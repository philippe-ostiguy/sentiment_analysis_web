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
""" This is the module to initialize and set the values of variables used across the project

"""
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import re
import requests
import bs4 as bs
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as opChrome
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as opFireFox
from decouple import config
import logging


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


class InitProject():
    """Class in which we set and/or initialize the values of the variables (attribute) for the entire project"""

    def __init__(self):
        """Built-in method to set and inialize the global values for the project

        Attributes
        -----------
        `self.columns_sentiment` : list
            list of columns used in the pandas Dataframe (`self.pd_stock_sentiment`) in which
            we stored the sentiment analysis for each stock.
            Text is the text in the post, twit. Probability is the probility of the sentiment (-1 to +1. -1 with 100%
            chance of a negative sentiment and +1 with a 100% of a positive sentiment. Directional is applicable only
            for Stockwits (user can choose 'bullish' or 'bearish' when creating a twit).
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. We can search for more than 24 hours ago
        `self.us_holidars` : list
            List that contains the US Stock Holiday
        `self.pd_stock_sentiment` : pandas.DataFrame
            Pandas DataFrame that contains the sentiment/mood for each stock we are webscrapping on social media
        `self.stock_dictionnary` : dict
            dictionary of stocks (ticker is the key) with keywords associated with them (item) that we are looking in
            the post. The items are one list per stock (key). This is the whole list we want to webscrap
            For reddit, we are searching with the keywords (values), whereas in Stocktwits and Twitter only with the
            key (ticker). On twitter and stocktwits, URL are based on the 'ticker', ex :
            https://twitter.com/search?q=%24gib&src=typed_query&f=live.
            If we know some stocks we want to webscrap, we must enter it as a ticker as a string (capitalisation) with
            the company name as a string. Ex: self.stock_dictionary = {'TSLA' : ['Tesla', 'TSLA']}
        `self.current_stock` : dict
            current dictionary of `self.stockdictionary` we are webscrapping data on the social media
        `self.pause_time` : long
            pause time when scrolling down the pageand pause between manipulations on browser to load. 
            We may need to increase this value as the page may be loaded at different time interval and needs to be 
            long enough :  https://selenium-python.readthedocs.io/waits.html
        `self.comment_source` : list
            source of comments/twits that we analyse the sentiment
        `self.pd_metrics` : pandas.DataFrame
            Pandas Dataframe with metrics from the results. Ex: Nb of comments, average sentiment per social media, etc.
        `self.keywords_to_remove` : list
            list of keyword to remove when we search for a stock on Reddit. Ex: we know that
            'Apple' is named 'Apple Inc.'. We want to remove the 'Inc' so that we only search for 'Apple' on reddit
        `self.total_comments` : int
            total comments for reddit
        `self.min_short` : int
            minimum acceptable thresold for shorted stocks. Ex: we will only webscrap data for a shorted stock if
            he has 30% of outstanding shares shorted.
        `self.min_cap` : int
            minimum stock capitalization to webscrap data. Ex: below 500M$ market cap, we don't webscrap
        `self.av_key` : str
            API key for Alpha Vantage
        `self.min_comments` : int
            Minimum number of comments to enter a trade. Ex : below 100 comments for all sources (reddit, stocktwits,
            twitter), we don't initiate a trade
        `self.min_sentiment` : int
            Minimum sentiment level to enter a trade. Ex: A sentiment level below -20%, we go bear, above +20%, we
            go bull.
        `self.short_level` : int
            Short level we use to get stock that we may trade (used in `stock_to_trade`). Ex: on Finviz, we get the stock
            we a short level of 30% or more of floating stocks. We will then webscrap data on these stocks and get
            sentiment analysis. If we use FinViz to get the shorted stocks (in `stock_to_trade.py`, the value most be
            either 5%, 10%, 15%, 20%, 25% or 30%.This is because the free version of Finviz only accepts these values.
        `self.min_sentiment_in` : int
            Minimum sentiment level to keep a trade when we already in. Ex: A sentiment level below -15%, we stay bear,
            above +15%, we stay bull
        `self.time_ago_trend` : int
            same as `self.time_ago` but for trending stock on stocktwits. It is lower than `self.time_ago` and should
            be around 4 to 6 hours (`self.time_ago_trending = 4 to 6`) as there are generally a lot more comments
            for the trending stocks on Stocktwits. We don't want to webscrap forever (1 day of data is a lot for
            the trending stock on Stocktwits)
        `self.time_ago_no_trend`
            same as `self.time_ago` but for none trending stock on Stocktwits (like highly shorted stock as shown on
            finviz). It should be higher than `self.time_ago_trend` as these stocks have generally less comments
            on stocktwits, twitter and reddit
        `self.trending_stock` : dict
            we say for each stock if it is a Stocktwits trending stock, so that we decide if we use `self.time_ago`
            or `self.time_ago_trending`
        """

        #list of variables we can change ourself. Be careful when changing the order of a list as we refer to item
        #number of a liste in the code to get the value
        self.columns_sentiment = ['text','probability','directional','source','user']
        self.columns_metrics = ["Total average sentiment","Total number of comments", "Stocktwits sentiment accuracy",
                                "Average sentiment for ", "Nb of comments for "]
        self.comment_source = ['reddit','stocktwit','twitter']
        self.keywords_to_remove = ['limited', 'Limited','Inc.','INC', 'Corporation', 'Corp.', 'Corp', 'Co.',
                                   'Ltd','ltd',',']
        self.time_ago = 0
        self.time_ago_no_trend = 7*24 #should be higher than `self.time_ago_trend`
        self.time_ago_trend = 6
        self.trending_stock  = {}
        self.pause_time = 2
        self.short_level = 30
        self.min_cap = 500*10**6
        self.min_comments = 60
        self.min_sentiment = 20
        self.min_sentiment_in = 15

        #we may change these variables but probably not
        self.subreddit = "wallstreetbets" #subreddit we webscrap data on in `reddit_api.py`
        self.limit = 100000 #max comments to webscrap on reddit in `reddit_api.py`

        self.stock_dictionnary = {} #list of stocks we webscrap. We get them in the package `stock_to_trade.py`

        #list of variables that are not necessary to change
        self.output_ = 'output/' #name of the folder where the output are stored
        self.results = 'results.csv' #name of the files with the `self.pd_metrics` results
        self.timer_= 'timer_.csv' #name of the files with the `self.pd_timer` results
        self.input = 'input/' #name of the folder where the input are stored
        self.position = 'positions.csv' #name of the files telling the position we have. We have a position if
                                        #the thresold are 'meet' (`self.min_comments` and `self.min_sentiment`
        #file with the results, ie nb of comments and sentiment analysis
        self.results_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.output_, self.results)
        #file with the time it took to run the script on each source (reddit, stocktwit, twitter)
        self.timer_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.output_, self.timer_)


        # list of variables that we should not set ourself
        self.us_holidays = []
        self.current_stock = '' #current stock we webscrap
        self.pd_stock_sentiment = pd.DataFrame(columns=self.columns_sentiment)
        self.driver_parameters = {} #parameters for the webdrivers (Chrome and Firefox). Parameters are in
        # `self.init_driver()`
        # fetching or not the data on the 'weekend discussion' post on wallstreetbet.
        self.check_weekend = False # False per default.
        self.pd_metrics = pd.DataFrame()
        self.pd_timer = pd.DataFrame(columns=self.comment_source)
        self.total_comments = []
        self.av_key = config('AV_KEY')
        self.logger_file = config('LOG_FILENAME') #file with error (traceback)
        self.twilio_sid = config('TWILIO_SID') #SID to use twilio API, to send SMS
        self.twilio_auth = config('TWILIO_AUTH') #AUTH to use twilio API, to send SMS
        self.to_phone=config('TO_PHONE') #phone number we send a SMS with Twilio
        self.from_phone=config('FROM_PHONE') #Number from where we send SMS with Twilio

    def __call__(self):

        # calling the functions
        self.get_us_holiday()
        self.init_driver()
        self.init_timer()
        #self.set_time_ago()
        self.create_columns()
        self.create_logger()


    def init_timer(self):
        """Initialize the values to 0 (first line) of self.pd_timer"""

        for source in self.comment_source:
            self.pd_timer.loc[0, source] = 0

    def create_columns(self):
        """Create new (appropriate) columns for the pd Dataframe metrics"""

        column_tempo = self.columns_metrics.copy()
        i = 0
        for source in self.comment_source:
            try:
                column_tempo[i*2+3] = self.columns_metrics[3] +source
            except:
                column_tempo.append(self.columns_metrics[3] +source)

            try:
                column_tempo[i*2+4] = self.columns_metrics[4] + source
            except:
                column_tempo.append(self.columns_metrics[4] +source)

            i+=1
        self.pd_metrics =self.pd_metrics.reindex(columns=column_tempo)

    def get_us_holiday(self):
        """Get the US Stock holidays """

        resp = requests.get('https://www.nyse.com/markets/hours-calendars')
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        # Grab the table with the US Stock holidays (first table)
        table = soup.find_all('table', {'class': 'table table-layout-fixed'})[0]
        if table == []:
            raise Exception("Table to get US stocks holiday in function `get_us_holiday()` does not exist")

        years_ = []

        # get the year in the header
        for headers_ in table.findAll('tr')[:1]:
            for header_ in headers_.findAll('th')[1:]:
                years_ += header_

        for holidays_ in table.findAll('tr')[1:]:

            i = 0
            for holiday_ in holidays_.findAll('td')[1:]:

                #remove white space
                text_tempo = holiday_.text
                text_ = holiday_.text.replace('  ', ' ')
                while text_ != text_tempo:
                    text_ = text_.replace('  ', ' ')
                    text_tempo = text_.replace('  ', ' ')

                if "—" in holiday_.text:
                    i += 1
                    continue

                month_ = text_.split(' ')[1]
                day_ = re.sub("[^0-9]", "",text_.split(' ')[2])
                year_ = years_[i]
                date_ = "-".join([year_, month_, day_])
                self.us_holidays.append(datetime.strptime(date_, '%Y-%B-%d'))

                i += 1

        if not self.us_holidays :
            raise Exception(f"List ``self.us_holidays {self.us_holidays} is empty in package `initialize.py`")

    def create_logger(self):
        """Create file and erase previous one if it exists"""
        #file = open('log.log',"w")
        file = open(self.logger_file,"w")
        file.close()
        #pass

    def init_driver(self):
        """Method to initialize the parameters for the drivers (Firefox and Chrome) """

        # Options for Chrome Driver
        self.options_chrome = opChrome()
        #self.options_chrome.add_argument("--disable-gpu")
        self.options_chrome.add_argument("--disable-extensions")
        self.options_chrome.add_argument("--no-sandbox")
        self.options_chrome.add_argument("--headless")
        #self.options_chrome.add_argument("--disable-dev-shm-usage")
        self.options_chrome.add_argument( "--window-size=1920,1080")


        #store options in dictinoary
        self.driver_parameters['options_chrome'] = self.options_chrome

        #Options for Firefox driver
        self.option_ff = opFireFox()
        self.option_ff.add_argument("--headless")
        self.option_ff.add_argument("--window-size=1920,1080")
        self.option_ff.add_argument("--no-sandbox")
        #self.option_ff.add_argument("--disable-dev-shm-usage")
        self.ff_language =  'en-US, en'

        #store options and language profile in dict
        self.driver_parameters['options_ff'] = self.option_ff
        self.driver_parameters['ff_language'] = self.ff_language


    def set_time_ago(self):
        """Modifiy `self.time_ago` depending if the current day is Monday (so that previous days are the weekend)
        anr/or if the current day is a US Stock Holiday"""

        today = date.today()
        yesterday = today - timedelta(days=1)

        # check if it Monday today
        if date.today().weekday() == 0:
            self.time_ago += 48  # add 48 hours because of Saturday and Sunday
            self.check_weekend = True  # fetching data on the 'weekend discussion' in wallstreetbet

        # check if yesterday was a holiday
        for date_ in self.us_holidays:
            if ((yesterday.month == date_.month) and (yesterday.year == date_.year) and
                    (yesterday.day == date_.day)):
                # if current days is Tuesday, then 2 days before was the weekend
                if date.today().weekday() == 1:
                    self.time_ago += 48
                    self.check_weekend = True  # fetching data on the 'weekend discussion' in wallstreetbet

                else:
                    self.time_ago += 24

class InitNewsHeadline():
    """Class that initializes global value for the module for sentiment analysis of news headline.
    It also use general method to initialize values.
   """

    def __init__(self):
        """Built-in method to inialize the global values for sentiment analysis of news headline

        Attributes
        -----------
        `self.start.date` : str
            start date of the training period. Must be within the last year for the free version of FinHub. Format
            must be "YYYY-mm-dd"
        `self.end_date` : str
            end date of the training period. Format must be "YYYY-mm-dd"
        `self.ticker` : list
            tickers on which we want to perform the test. Can be one ticker in form of a list as well as a list
            of tickers like the s&p 500.
        `self.db_name` : str
            name of the sqlite3 database
        `self.web_scrap_name` : str
            name for the web_scrapping package (used for the folder directory name)
        `self.file_name` : str
            name of the file (db) including the directory. It takes into account the `self.start_date` and
            `self.end_date`
        `self.news_header` : list
            list containing the columns name returned (in order) by the FinnHub's API
        `self.start_date_` : datetime object
            same thing as `start_date` but as a datetime object
        `self.end_date_` : datetime object
            same thing as `start_date` but as a datetime object
        `self.web_scraping` : boolean
            decides to run or not the webscraping package in the `main.py` module
        `self.end_date_` : datetime object
            same thing as `start_date` but as a datetime object
        """

        # initialize value here
        self.start_date = "2021-08-06"
        self.end_date = "2021-08-10"
        self.tickers = ['FSR']
        self.db_name = 'financial_data.db'
        self.web_scrap_name = 'web_scrapping'
        self.start_date_ = datetime.strptime(self.start_date, "%Y-%m-%d")  # datetime object
        self.end_date_ = datetime.strptime(self.end_date, "%Y-%m-%d")  # datetime object
        self.web_scraping = True
        self.sentiment_analysis = True

        self.file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)),self.web_scrap_name, 'output',
                                          self.start_date + '_' + self.end_date)
        Path(self.file_name).mkdir(parents=True, exist_ok=True)  # create new path if it doesn't exist
        self.file_name = os.path.join(self.file_name, 'financial_data.db')
        self.delta_date = abs((self.end_date_ - self.start_date_).days)  # number of days between 2 dates

        #Headers for the FinnHub API
        self.news_header = ['category', 'datetime','headline','id','image','related','source','summary','url']

        try:
            self.start_date_ > self.end_date_
        except:
            print("'start_date' is after 'end_date'")

class InitStockTwit():
    """Class that initializes global value for the module sentiment analysis of Stock Twits
    """

    def __init__(self):
        """Built-in method to inialize the global values for the module sentiment analysis of Stock Twits

        Attributes
        ----------

        `self.columns_twits` : list
            List of name of the columns we store the information from twits
        `self.positive_level` : float
            Positive sentiment level at which we take a long position ona  stock
        `self.min_sample` : int
            Minimum

        """
        self.columns_twits = ['time_published', 'directional', 'text']
        self.positive_level = .6
        self.min_sample = 60

class InitReddit():
    """Class that initializes global value for the module sentiment analysis of Reddit
    """

    def __init__(self):
        """Built-in method to inialize the global values for the module sentiment analysis of Stock Twits

        Attributes
        ----------

        `self.columns_twits` : list
            List of name of the columns we store the information from twits
        `self.positive_level` : float
            Positive sentiment level at which we take a long position ona  stock
        `self.min_sample` : int
            Minimum

        """
        self.columns_twits = ['time_published', 'directional', 'text']
        self.positive_level = .6
        self.min_sample = 60