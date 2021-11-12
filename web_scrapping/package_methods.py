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

from datetime import datetime
import re
import emoji
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


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

    #replace emojis for text
    text_to_clean = emoji.demojize(text_to_clean, delimiters=(" ", " "))

    #remove newline
    text_to_clean = re.sub(r'\n\d', ' ', text_to_clean).replace("\n"," ")

    # remove mentions tickers ($ followed by ticker in Stocktwits)
    text_to_clean = re.sub(r'[$][A-Za-z][\S]*', ' ', text_to_clean)

    #remove hastag and @ including text
    text_to_clean = re.sub(r'[#][A-Za-z0-9][\S]*', ' ', text_to_clean)
    text_to_clean = re.sub(r'[@][A-Za-z0-9][\S]*', ' ', text_to_clean)

    # remove url
    text_to_clean = re.sub(r'\\s*[^[:space:]/]+/[^[:space:]/]+', "", text_to_clean)
    text_to_clean = re.sub('https?:\/\/[a-zA-Z0-9@:%._\/+~#=?&;-]*', ' ', text_to_clean)

    #Lower case
    #text_to_clean = text_to_clean.lower()

    # Replace everything not a letter or apostrophe with a space
    #text_to_clean = re.sub('[^a-zA-Z\']', ' ', text_to_clean)

    # Remove single letter words
    #text_to_clean = ' '.join([word for word in text_to_clean.split() if len(word) > 1])

    #remove punctuations
    text_to_clean = ' '.join(re.sub("[\.\,\!\?\:\;\-\=]", " ", text_to_clean).split())

    # remove duplicated whitespaces
    text_to_clean = text_to_clean.replace("  ", " ")

    return text_to_clean

def webscrap_content(**kwargs):
    """Method to web-scrap content on Stocktwits
    """

    kwargs['driver'].get(kwargs['end_point'])
    time.sleep(kwargs['pause_time'])
    scroll_to_value(**kwargs)
    time.sleep(kwargs['pause_time'])
    return kwargs['driver'].find_elements_by_xpath(kwargs['posts_to_return'])

def scroll_to_value(**kwargs):
    """Method that scrolls until we find the value, then stops. It search for a date and the class containg
    the date"""


    wait = WebDriverWait(kwargs['driver'], kwargs['pause_time'])
    element_ = None

    while not element_:

        kwargs['driver'].execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            element_ = wait.until(EC.presence_of_element_located((By.XPATH,kwargs['date_to_search'])))

        except TimeoutException:
            pass