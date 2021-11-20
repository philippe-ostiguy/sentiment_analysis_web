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

"""Module to webscrap data on Reddit (wallstreetbets)"""


from datetime import datetime, timedelta, time, date
import time
import pandas as pd
import os
import web_scrapping.package_methods as pm
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import web_scrapping.package_methods as pm

class RedditApi_():
    """Class to webscrap data on Reddit using Selenium. It stores it in a pandas dataFrame.
    Things to know :
    - It's made for an analysis on a daily basis (by default, but can be changed it we modify `self.time_ago`
    - From Tuesday to Friday, we try to get the last 24 hours of comments
    - On Monday, we get the comments posted during the weekend
    """

    def __init__(self,init,init_sentiment):
        """
        Parameter
        ----------
        `init` : cls
            class from the module `initialize.py` that initializes global variables for the project
        `init_sentiment` : cls
            class from the module `twits_analysis` with the Twitter Roberta based transformer model already initialized
            and ready to perform sentiment analysis

        Attributes
        ----------
        `self.init.current_stock` : str
            current stock we webscrap

        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. This value must be 1 hour or more as the time
            format in Reddit is in hours (under 24 hours) and days (24 hours or more after the post was created).
            By default, the value is 24, and should not be changed. If it is changed, the funciton `self.set_time_ago()`
            should be reviewed.
            The program is made to search the last 24 hours and
            it operates this way. Ex: the function `self.set_time_ago()` changes `self.time_ago` depending if we are on
            Monday or on a US Stock holiday and will fetch accordingly.
        `self.api_endpoint` : str
            API's endpoint parameter
        `self.class_time` : str
            Name of the class in reddit containing the published time of a reddit post
        `self.class_comments` : str
            Name of the class in Reddit containing the comments (wihin a post)
        `self.class_more_comments ` : str
            Name of the class in Reddit for the more comments button (load more comments)
        `self.reddit_endpoint` : str
            Endpoint of the stock we want to webscrap
        `self.min_replies` : int
            minimum of reply in reddit to click on it. Ex : we don't want to click on all the '1 more reply' as it takes
            times
        `self.date_` : str
            date until which we webscrap data
        `self.buffer_time_size` : int
            buffer (number) to fetch the dates we want. Ex :  If the buffer is 3, and `self.time_ago` is 5 hours,
            it will also stop fetching the data if it sees 6 hours or 7 hours in the post and set the value
            `self.date__` accordingly
        `self.date__` : str
            list of date we try to find in a post which will make the fetch stops if one of the date is found.
            The lenght of the list depends on `self.buffer_time_size` and is set in function `self.set_buffer_time_size`
        `self.daily_discussion_url` : str
            URL on Reddit to obtain the daily discussion post and links
        `self.weekend_discussion_url` : str
            URL on reddit to obtain the weekend discussion post and links
        `self.class_post` : str
            class in reddit (in DOM) for the post (get URL, and time it was created)
        """

        super().__init__()

        #We should touch these data. They come from the classes where we initialize the data
        self.init = init #giving the values of class `init` to `self.init` variable (pv for project variables)
        self.roberta = init_sentiment #giving the values of class `init_sentiment` to `self.roberta` variable


        self.date_ = ""
        self.reddit_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/'
        self.tempo_endpoint = ''  # Temporary endpoint - we add the ticker we want to webscrap at the end of


        self.daily_discussion_url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair_name%3A%22Daily' \
                                    '%20Discussion%22&restrict_sr=1&sr_nsfw=&sort=new'
        self.weekend_discussion_url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair_name' \
                                      '%3A%22Weekend%20Discussion%22&restrict_sr=1&sr_nsfw=&sort=new'
        self.class_post ='_3jOxDPIQ0KaOWpzvSQo-1s'

        self.class_time = '_3yx4Dn0W3Yunucf5sVJeFU'  # time
        self.class_more_comments = '_3sf33-9rVAO_v4y0pIW_CH'
        self.class_comments = '_3cjCphgls6DH-irkVaA0GM'  # post
        self.reddit_posts_url = [] #list of url posts we will webscrap data from on Reddit
        self.reddit_comments= [] #list that contains the comments (text only)

        self.min_replies = 100
        self.min_reply_list = []  # associated list with the `self.min_replies` attribute
        self.rejected_replies_list = ""  # list of MoreComments buttons we don't click on it. It depends of
        self.buffer_time_size = 10
        self.date__ = ""
        self.reddit_dict_ = {}

    def webscrap(self):
        """Performs all the method necessary to webscrap the content on reddit's posts and analyse the mood of the
        comments"""

        self.time_to_search()
        self.rejected_replies()
        self.get_posts()
        self.scroll_to_end()

    def get_posts(self):
        """ Method to get the posts on wallstreet so that we get comments from the last 24 hours. This is
        approximately, some comments will be a little bit older than 24 hours as when we fetch data from a post, we
        fetch all the data.

        It depends on the creation of the post. We webscrap two types of post everyday (Tuesday to Friday),
        which makes 3 posts in total to webscrap. One of them is named 'Daily Discussion' and is generally created
        around 6h00 am in the morning (we webscrap 2 of them per day). The other one is called 'What Are Your
        Moves Tomorrow', and is generally created around 4h00 pm.
        """

        #save the posts we will webscrap data from.
        #This if for the posts that we webscrap data from Tuesday to Friday
        self.init.driver.get(self.daily_discussion_url)
        time.sleep(2)
        element_to_search = '//a[contains(@class,"{}") and ({})]'.format(self.class_post,self.date__)
        #posts url
        self.reddit_posts_url += [post.get_attribute("href") for post in
                                   self.init.driver.find_elements_by_xpath(element_to_search)]

        if self.init.check_weekend:
            self.init.driver.get(self.weekend_discussion_url)
            time.sleep(2)
            element_to_search = '//a[contains(@class,"{}") and ({})]'.format(self.class_post, self.date__)
            self.reddit_posts_url += [post.get_attribute("href") for post in
                                       self.init.driver.find_elements_by_xpath(element_to_search)]

    def time_to_search(self):
        """Method that set the variable `self.date__` depending on  how far we need data `self.time_ago`.
        It will only fetch in the posts that time published (of post) >= `self.time_ago`
         """

        writing_minutes = True
        i = 1

        #writing time for minutes
        while True:
            str_tempo = str(i)
            if i == 1:
                self.date__ += "".join(['./text() = ', '"', str_tempo, ' minute ago"'])
            else :
                self.date__ += "".join([' or ./text() = ', '"', str_tempo, ' minutes ago"'])
            i += 1
            #60 seconds in 1 minute
            if i == 60:
                break

        i = 1
        j = 1
        #writing time for hours and days
        while (i- 1)  < self.init.time_ago:
            str_tempo = str(i)
            #write time in hours
            if i == 1:
                self.date__ += "".join([' or ./text() = ', '"', str_tempo, ' hour ago"'])
            elif i < 24 :
                self.date__ += "".join([' or ./text() = ', '"', str_tempo, ' hours ago"'])
            #write time in days
            else:
                str_tempo = str((i) // 24)
                if j == 1 :
                    self.date__ += "".join([' or ./text() = ', '"', str_tempo, ' day ago"'])
                    j+=1
                else :
                    self.date__ += "".join([' or ./text() = ', '"', str_tempo, ' days ago"'])
                    j+=1
                i += 23  # 24 hours in 1 day
            i += 1

    def rejected_replies(self):
        """ Method to make a list of the 'MoreComments' buttons we don't click on. It depends on the number on replies
        `self.min_replies`. Ex: We may not want to click on all more comments button '1 more reply' as it takes times.
        """

        # We put in `self.rejected_replies_list` all the 'moreComments' we are not allowed to click on
        i = 1

        while i < self.min_replies:
            if i == 1:
                self.rejected_replies_list += ''.join([' and not(./div/p/text() = ', '"', str(i), ' more reply', '")'])
            else:
                self.rejected_replies_list += ''.join(
                    [' and not(./div/p/text() = ', '"', str(i), ' more replies', '")'])

            i += 1

    def loop_reddit_post(func):
        """ Decorator that web-scrap content on all reddit posts that we choose using Selenium """

        def wrapper_(self):

            for url_post in self.reddit_posts_url:
                self.init.driver.get(url_post)
                time.sleep(2)
                func(self)
                self.reddit_comments += [comment.text for comment in self.init.driver.find_elements_by_xpath(
                    "//div[contains(@class,'{}')]".format(self.class_comments))]
        return wrapper_

    def loop_comments(func):
        """Decorator to loop throught the comments that we webscrap"""

        def wrapper_(self):
            self.reddit_dict_ = {}
            for comment in self.reddit_comments:
                # check if the post contains the stock (keywords) we are looking for
                for stock,keywords in self.init.stock_dictionnary.items():
                    if stock == self.init.current_stock:
                        #check if the comment contains at least one of the keyword
                        if any(keyword in comment for keyword in keywords):

                            func(self,comment)
                            break # not analyzing the same post twice (in case we have more than 1 keyword)
            self.init.pd_stock_sentiment = self.init.pd_stock_sentiment.drop_duplicates\
                (subset=self.init.columns_sentiment[0], keep="first")
            return self.init.pd_stock_sentiment
        return wrapper_

    @loop_comments
    def write_values(self,comment):
        """Method to determine if mood of each comment (positive, negative) with a score between -1 and 1
         (-1 being the most negative and +1 being the most positive and write different values in the
         pandas DataFrame `self.pd_stock_sentiment`"""

        self.init.pd_stock_sentiment = pm.write_values(comment = comment,pv = self.init,
                                                     model = self.roberta,source = 0,dict_ = self.reddit_dict_)

    @loop_reddit_post
    def scroll_to_end(self):
        """ method that scroll to the end of the page to load all first-level comments on a post.
         - We use the method `wait` as the page may load at different time intervals :
         https://selenium-python.readthedocs.io/waits.html
         - If there is a button 'MoreComments', we click on it to load more comments :
        https://praw.readthedocs.io/en/stable/code_overview/models/more.html#praw.models.MoreComments
        - We don't fetch second-level comments (comments under first-level comment) as it will take to much time)
        """

        wait = WebDriverWait(self.init.driver, self.init.pause_time)
        element = None
        screen_height = self.init.driver.execute_script("return window.screen.height;")  # return window screen height
        button_click_text = '//div[@class = "{}" and (contains(@id,"moreComments"))'.format(self.class_more_comments) \
                            + self.rejected_replies_list
        i = 1

        while not element:

            # go to section in window according to `i` and `screen_height`
            self.init.driver.execute_script("window.scrollTo(0, {screen_height}*{i});"
                                       .format(screen_height=screen_height, i=i))
            # return DOM body height
            scroll_height = self.init.driver.execute_script("return document.body.scrollHeight;")

            # check if we are a the end of the page
            if (screen_height) * i > scroll_height:
                # the scrolling may go to quickly and arrives at the end of the page prematurely
                try:
                    button_click = wait.until(EC.presence_of_element_located((By.XPATH, button_click_text + ']')))
                    button_click.click()

                except:
                    break

            # Check if there is a button 'MoreComments' and click on it to load more comments
            try:
                button_click = wait.until(EC.presence_of_element_located((By.XPATH, button_click_text + ']')))
                button_click.click()
                i-=1

            except:
                pass


            i+=1




