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
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager



class RedditApi_():
    """Class to webscrap data on Reddit using Selenium and then, analyze the comments (sentiment analysis).
    Things to know :
    - It's made for an analysis on a daily basis (by default, but can be changed it we modify `self._time_ago`
    - From Tuesday to Friday, we try to get the last 24 hours of comments
    - On Monday, we get the comments posted during the weekend
    """

    def __init__(self,pv):
        """
        Attributes
        ----------

        `self.stock_keywards` : str
            keywords for the stock that we want to webscrap data
        `self.limit_comments` : int
            maximum number of comments to fetch (default is 100. In general, max number allowed is 1000 :
            https://praw.readthedocs.io/en/latest/code_overview/other/listinggenerator.html#praw.models.ListingGenerator)
        `self.reddit_result` : pandas.DataFrame
            results from wbescrapping reddit (comment, time published, score)
        `self.reddit_columns` : list
            type of values we want to store from webscrapping reddit
            (possibilities : https://praw.readthedocs.io/en/latest/code_overview/models/comment.html#praw.models.Comment)
        `self._time_ago` : int
            Number of hours in the past we want to webscrape the data. This value must be 1 hour or more as the time
            format in Reddit is in hours (under 24 hours) and days (24 hours or more after the post was created).
            By default, the value is 24, and should not be changed. The program is made to sear`ch the last 24 hours and
            it operates this way. Ex: the function `self.set_time_ago()` changes `self._time_ago` depending if we are on
            Monday or on a US Stock holiday and will fetch accordingly.
        self.sort_comments_method : str
            how we sort comments in a submission (see this link and section 'property comments' :
            https://praw.readthedocs.io/en/latest/code_overview/models/submission.html)
        `self.api_endpoint` : str
            API's endpoint parameter
        `self.driver_file_name` : str
            Chrome driver's file name
        `self.scroll_pause_time` : long
            pause time when scrolling down the page. We may need to increase this value as the page may be loaded
            at different time interval and needs to be long enough :  https://selenium-python.readthedocs.io/waits.html
        `self.class_time` : str
            Name of the class in reddit containing the published time of a reddit post
        `self.class_comments` : str
            Name of the class in Reddit containing the comments (wihin a post)
        `self.class_more_comments ` : str
            Name of the class in Reddit for the more comments button (load more comments)
        `self.reddit_endpoint` : str
            Endpoint of the stock we want to webscrap
        `self.number_of_submissions` : int
            number of submissions in reddit we want to webscrap data
        `self.min_replies` : int
            minimum of reply in reddit to click on it. Ex : we don't want to click on all the '1 more reply' as it takes
            times
        `self.date_` : str
            date until which we webscrap data
        `self.class_submission_time` : str
            class to get the time a submission was published
        `self.buffer_time_size` : int
            buffer (number) to fetch the dates we want. Ex :  If the buffer is 3, and `self._time_ago` is 5 hours,
            it will also stop fetching the data if it sees 6 hours or 7 hours in the post and set the value
            `self.date__` accordingly
        `self.date__` : str
            list of date we try to find in a post which will make the fetch stops if one of the date is found.
            The lenght of the list depends on `self.buffer_time_size` and is set in function `self.set_buffer_time_size`
        `self.daily_discussion_url` : str
            URL on Reddit to obtain the daily discussion post and links
        `self.weekend_discussion_url` : str
            URL on reddit to obtain the weekend discussion post and links
        `self.driver` : selenium driver
            Selenium from driver to webscrap the data
        `self.class_post` : str
            class in reddit (in DOM) for the post (get URL, and time it was created)

        """

        self.stock_keywords = ['TSLA', 'Tesla']
        self._time_ago = 24
        self.sort_comments_method = "new"
        self.date_ = ""

        self.us_holiday = pv.us_holidays #list of US Stock Holiday in Datetime
        self.us_holiday += date.today()

        self.reddit_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/'
        self.tempo_endpoint = ''  # Temporary endpoint - we add the ticker we want to webscrap at the end of
        # self.stock_endpoint
        self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chromedriver')
        # self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'geckodriver')
        self.scroll_pause_time = 1

        self.daily_discussion_url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair_name%3A%22Daily' \
                                    '%20Discussion%22&restrict_sr=1&sr_nsfw=&sort=new'
        self.weekend_discussion_url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair_name' \
                                      '%3A%22Weekend%20Discussion%22&restrict_sr=1&sr_nsfw=&sort=new'
        self.class_post ='_3jOxDPIQ0KaOWpzvSQo-1s'


        self.class_time = '_3yx4Dn0W3Yunucf5sVJeFU'  # time
        self.class_time_whole = '_1a_HxF03jCyxnx706hQmJR'  # class time with more details
        self.class_more_comments = '_3sf33-9rVAO_v4y0pIW_CH'
        self.class_comments = '_3cjCphgls6DH-irkVaA0GM'  # post
        self.class_submission_time = '_3jOxDPIQ0KaOWpzvSQo-1s'
        self.list_reddit_posts = [] #list of posts we will webscrap data from on Reddit
        self.reddit_comments= [] #list that contains the comments

        self.min_replies = 100
        self.min_reply_list = []  # associated list with the `self.min_replies` attribute
        self.rejected_replies_list = ""  # list of MoreComments buttons we don't click on it. It depends of
        self.buffer_time_size = 10
        self.date__ = ""

        self.reddit_result = pd.DataFrame()
        self.reddit_columns = ['comment', 'time_published', 'comment_score']
        self.number_of_submissions = 5

    def __call__(self):

        self.time_to_search()
        self.init_driver()
        self.get_posts()
        self.webscrap_content()
        self.analyse_content()

        self.rejected_replies()

    def init_driver(self):

        # Options for Chrome Driver
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")
        # Pass the argument 1 to allow notifications and 2 to block them
        option.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })

        # self.driver = webdriver.Chrome(chrome_options=option, executable_path=self.driver_file_name)
        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en-US, en')
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile)

    def set_time_ago(self):
        """Modifiy `self._time_ago` depending if the current day is Monday (so that previous days are the weekend)
        anr/or if the current day is a US Stock Holiday"""
        
        #check if it Monday
        if date.today().weekday() == 0:
            self._time_ago += 48 #add 48 hours because of Saturday and Sunday

        #check if current day is a holiday
        if date.today() in self.us_holiday:
            if date.today().weekday() == 1:
                self._time_ago += 48
            else :
                self._time_ago += 24


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
        self.driver.get(self.daily_discussion_url)
        time.sleep(2)

        element_to_search = '//a[contains(@class,"{}") and ({})]'.format(self.class_post,self.date__)
        self.list_reddit_posts += self.driver.find_elements_by_xpath(element_to_search)

        t = self.list_reddit_posts[0].text
        d = self.list_reddit_posts[1].text
        url_ = self.list_reddit_posts[0].get_attribute("href")
        d = 5

    def time_to_search(self):
        """Method that set the variable `self.date__` depending on  how far we need data `self._time_ago`.
        It will only fetch in the posts that time published (of post) >= `self._time_ago`
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
        while (i- 1)  < self._time_ago:

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

    def webscrap_content(self):
        """Method to web-scrap content on Reddit using Selenium
        """

        self.tempo_endpoint = \
        'https://www.reddit.com/r/wallstreetbets/comments/qnjay6/weekend_discussion_thread_for_the_weekend_of/?sort=new'
        self.driver.get(self.tempo_endpoint)
        time.sleep(2)

        start_time = time.time()
        self.scroll_to_value(self.driver)
        end_time = time.time()
        difference = end_time - start_time
        self.reddit_comments = self.driver.find_elements_by_xpath(
            "//div[contains(@class,'{}')]".format(self.class_comments))

    def analyse_content(self):
        """Method to determine if mood of each comment (positive, negative) with a score between -1 and 1
         (-1 being the most negative and +1 being the most positive """

        reddit_dictionary = {}  # dictionary with information from twits
        i = 0

        for reddit in self.reddit_comments:
            # skip the stickied comment
            if i == 0:
                i += 1
                continue
            i += 1

            # check if the post contains the stock (keywords) we are looking for
            for keyword in self.stock_keywords:
                if keyword in reddit.text:
                    break  # not analyzing the same post twic (in case we have more than 1 keyword)

            # remove all unescessary text (emoji, \n, other symbol like $)
            reddit_tempo = pm.text_cleanup(reddit.text)

            reddit_dictionary[self.reddit_columns[0]] = reddit_tempo

            self.reddit_result = self.reddit_result.append(reddit_dictionary, ignore_index=True)

        t = 5

    def scroll_to_value(self):
        """ method that scroll the page until the value(s) is (are) found in DOM (@class `self.class_time`
        and the date `self.date_`).

         - We use the method `wait` as the page may load at different time intervals :
         https://selenium-python.readthedocs.io/waits.html
         - If the date is found, we have to make sure that it's found in the class `self.class_time`
        (ex : if we search  for '2d' to get the previous 2 days data, if in a post there is '2d' in the text (text()),
        then it will stop searching for the date)
         - If there is a button 'MoreComments', we click on it to load more comments :
        https://praw.readthedocs.io/en/stable/code_overview/models/more.html#praw.models.MoreComments
        """

        wait = WebDriverWait(self.driver, self.scroll_pause_time)
        element = None
        screen_height = self.driver.execute_script("return window.screen.height;")  # return window screen height
        i = 1
        button_click_text = '//div[@class = "{}" and (contains(@id,"moreComments"))'.format(self.class_more_comments) \
                            + self.rejected_replies_list

        date_searching = '//span[@class = "{}" and ./a[contains(@id, "CommentTopMeta")] and ({}) and not ' \
                         '(./span/text() = "Stickied comment")]'.format(self.class_time_whole, self.date__)

        is_clicking = False  # not clicking on a button by default

        while not element:

            # go to section in window according to `i` and `screen_height`
            self.driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
            # return DOM body height
            scroll_height = self.driver.execute_script("return document.body.scrollHeight;")

            i += 1
            is_clicking = False

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
                is_clicking = True

            except:
                pass