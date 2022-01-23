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
""" Methods used across the package wbe_scrapping"""

from datetime import datetime
import re
import emoji
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.options import Options as opChrome
from selenium.webdriver.firefox.options import Options as opFireFox


def delta_date(start_date,end_date):
    """Function that returns the number of days between 2 dates """

    return abs((datetime.strptime(start_date, "%Y-%m-%d") - datetime.strptime(end_date, "%Y-%m-%d")).days)

def get_data(dict,keys_):
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
        new_dict[key]=dict[key]
    return new_dict

def text_cleanup(text_to_clean):
    """clean unwnanted part in string (html, emoji, newline) for sentiment analysis"""

    # LIGHT DATA CLEANING
    """
    According to this post : https://towardsdatascience.com/part-1-data-cleaning-does-bert-need-clean-data-6a50c9c6e9fd
     and some test I did in project `sentiment_analysis_text`, light data cleaning gives better results than heavy 
     cleaning (removing hastage, @ and $ is not necessary as well as transforming emoji to text (package emoji and 
    function demojize)
    """

    # Lower case
    text_to_clean = text_to_clean.lower()

    # remove newline
    text_to_clean = re.sub(r'\n\d', ' ', text_to_clean).replace("\n", " ")

    # remove url
    text_to_clean = re.sub(r'\\s*[^[:space:]/]+/[^[:space:]/]+', "", text_to_clean)
    text_to_clean = re.sub('https?:\/\/[a-zA-Z0-9@:%._\/+~#=?&;-]*', ' ', text_to_clean)

    # Text cleaning
    text_to_clean = re.sub(r'\'\w+', '', text_to_clean)
    text_to_clean = re.sub(r'\w*\d+\w*', '', text_to_clean)
    text_to_clean = re.sub(r'\s{2,}', ' ', text_to_clean)
    text_to_clean = re.sub(r'\s[^\w\s]\s', '', text_to_clean)

    # remove white space
    text_to_clean = text_to_clean.replace("  ", " ")

    return text_to_clean

def initialise_driver(which_driver,driver_parameters):
    """Method to initialize the drivers of our choice (Firefox or Chrome) with parameters defined in `initialize.py`

    Parameters
    ----------
    `which_driver` : str
        Which driver we want to use between
    `driver_parameters` : dict
        Parameters used to initialize the driver. Ex: option, language settings, etc.
    """
    if which_driver == 'chrome':

        return webdriver.Chrome(chrome_options=driver_parameters['options_chrome'],
                                  executable_path=ChromeDriverManager().install())

    if which_driver == 'firefox':
        profile_ff = webdriver.FirefoxProfile()
        profile_ff.set_preference('intl.accept_languages', driver_parameters['ff_language'])
        return webdriver.Firefox(options = driver_parameters['options_ff'],firefox_profile=profile_ff,
                                           executable_path=GeckoDriverManager().install())


def webscrap_content(which_driver,posts_to_return,end_point,pause_time,date_to_search,driver_parameters,
                     is_twitter=False,stocktwit_class = None):
    """Method to web-scrap content on Stocktwits
    """

    twitter_post =[]
    driver = initialise_driver(which_driver,driver_parameters)
    driver.get(end_point)
    twitter_post = scroll_to_value(driver,posts_to_return,end_point,pause_time,date_to_search,is_twitter,
                                   stocktwit_class)
    time.sleep(pause_time)
    driver.quit()

    return twitter_post

def scroll_to_value(driver,posts_to_return,end_point,pause_time,date_to_search,is_twitter,stocktwit_class):
    """Method that scrolls until we find the value, then stops. It search for a date and the class containg
    the date"""

    wait = WebDriverWait(driver, pause_time)

    element_ = None
    exist = None
    twitter_tempo = []
    twitter_post = []
    while not element_:
        #we need to make it sleep, (between 1 and 2 minimum) otherwise the browser doesn't have enough time to load
        time.sleep(1.5)
        try:
            element_ = wait.until(EC.presence_of_element_located((By.XPATH,date_to_search)))
        except TimeoutException:
            pass

        #need to do it every time on twitter as it doesn't load all the DOM from bottom to top
        if is_twitter:
            try:

                twitter_post += [post.text for post in driver.find_elements_by_xpath(posts_to_return)]

            #it means that the page doesn't exist and will generate an error
            except:
                pass

        #here we check if we are on a page that is empty on stocktwit (it exists!) so that we don't scroll down
        # forever
        if not is_twitter:
            try :
                exist = wait.until(EC.presence_of_element_located((By.XPATH,stocktwit_class)))
            except:
                element_ = True
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    #putting the DOM elements (twits) in a dictionary (DOM elements is loaded from bottom to top)
    if not is_twitter:
        #sometimes we may get an error in stocktwits when there are too many posts. Also, if between the time we
        #reach the desired element (above `while not element_`) and we save the text in a list, there are new posts
        #(too many), it may generates an error. In that case, we return the list empty
        try :
            twitter_post += [post.text for post in driver.find_elements_by_xpath(posts_to_return)]
        except :
            return []
    return twitter_post

def write_values(comment, pv, model,source, dict_):
    """Method to determine if mood of each comment (positive, negative) with a score between -1 and 1
     (-1 being the most negative and +1 being the most positive and write different values in the
     pandas DataFrame `self.pd_stock_sentiment`"""

    # remove all unescessary text (transform emoji, remove \n, remove other symbol like $)
    tempo_comment = text_cleanup(comment)
    # if it's empty after cleaning, just continue, don't save/analyse the comment
    if not tempo_comment == '':
        dict_[pv.columns_sentiment[0]] = tempo_comment
        dict_[pv.columns_sentiment[1]] = model.roberta_analysis(tempo_comment)
        dict_[pv.columns_sentiment[3]] = pv.comment_source[source]
        pv.pd_stock_sentiment = pv.pd_stock_sentiment.append \
            (dict_, ignore_index=True)

    return pv.pd_stock_sentiment


def decorator_timer(source):
    """Decorator to time how long a function takes to execute

    Sources nb are in `initialise.py` (reddit, twitter and stocktwits)"""

    def timer(func):
        def wrapper_timer(self):
            start_time = time.time()
            func(self)
            end_time = time.time()
            elapse_time = end_time - start_time
            self.init.pd_timer.loc[0, self.init.comment_source[source]] += elapse_time
            return self.init.pd_stock_sentiment
        return wrapper_timer
    return timer