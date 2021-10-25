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

"""Module that makes requests to the Reddit API"""

import requests
from datetime import datetime, timedelta,time
import time
from dateutil.relativedelta import relativedelta
from decouple import config
import pandas as pd
import praw
import os
from praw.models import MoreComments
import web_scrapping.package_methods as pm
from selenium import webdriver
from collections import defaultdict
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains



class RedditApi_():
    """Class to make requests to the Reddit API. Thing to know :
    -Max 60 requests per minute : https://www.reddit.com/r/redditdev/comments/gz01fo/data_rate_limit_more_than_60_requests_per_minute/
    -Max 100 comments per request. The Package PRAW (to make API requests to Reddit) will stop making API calls
    if there is more than 60 requests per minute made. It will resume doign API calls by itself :
    https://www.reddit.com/r/redditdev/comments/l4uty1/what_is_the_max_number_of_comments_im_able_to/ +
    https://praw.readthedocs.io/en/latest/code_overview/other/listinggenerator.html?highlight=1000
    -`submission.comments.replace_more(limit=None)` retrieve additional comments (with the button in the UI
    'load comments' or 'more replies') up to 100 commetns at a time

    """

    def __init__(self):
        """
        Attributes
        ----------
        `self.username`,`self.password`, `self.client_id`,`self.client_secret`,`self.user_agent` : str
            Parameters to login to the Reddit API
        `self.subreddit` : str
            Subreddit we want to webscrap data
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
        `self.time_ago` : int
            Number of hours in the past we want to webscrape the data. This value must be 1 hour or more as the time
            format in Reddit is in hours (under 24 hours) and days (24 hours or more after the post was created)
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
            Name of the class in Stocktwits containing the published time of a reddit post
        `self.class_post` : str
            Name of the class in Reddit containing the text of the post
        `self.class_more_comments ` : str
            Name of the class in Reddit for the more comments button (load more comments)
        `self.reddit_endpoint` : str
            Endpoint of the stock we want to webscrap
        `self.buffer_date` : int
            nb of values we use for `self.date_` as a buffer to search the date we want in posts (function :
            `self.convert_time()`)
        `self.date__`: list
            list that contains the dates until which we will look for the data
        `self.number_of_submissions` : int
            number of submissions in reddit we want to webscrap data
        `self.min_replies` : int
            minimum of reply in reddit to click on it. Ex : we don't want to click on all the '1 more reply' as it takes
            times
        """

        self.username = config('USERNAME_REDDIT')
        self.password = config('PASSWORD_REDDIT')
        self.client_id =config('CLIENT_ID_REDDIT')
        self.client_secret=config('CLIENT_SECRET_REDDIT')
        self.user_agent=config('USER_AGENT_REDDIT')

        self.subreddit = 'wallstreetbets'
        self.stock_keywords = ['TSLA','Tesla']
        self.time_ago =24
        self.sort_comments_method = "new"
        self.buffer_date = 5
        self.date__ = []

        self.reddit_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/'
        self.tempo_endpoint = '' #Temporary endpoint - we add the ticker we want to webscrap at the end of
                                 #self.stock_endpoint
        #self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chromedriver')
        self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'geckodriver')
        self.scroll_pause_time = 0.5
        self.class_time = '_3yx4Dn0W3Yunucf5sVJeFU' #time
        self.class_whole_post = '_3tw__eCCe7j-epNCKGXUKk' #whole post
        self.class_more_comments ='_3_mqV5-KnILOxl1TvgYtCk'
        self.class_post = '_3cjCphgls6DH-irkVaA0GM' #post
        self.min_replies = 100
        self.replies_buffer = 30000 #max numbers of comments we put in the contains to search for a min numbers of comments
        self.min_reply_list = [] #associated list with the `self.min_replies` attribute
        self.allowed_replies_list = "" #list of MoreComments buttons we don't click on it. It depends of
                                        #`self.min_replies`

        self.reddit_result = pd.DataFrame()
        self.reddit_columns = ['comment', 'time_published','comment_score']
        self.number_of_submissions = 5

    def __call__(self):

        self.convert_time()
        self.accepted_replies()
        # Authentical with OAuth and Reddit API
        reddit = praw.Reddit(client_id=self.client_id,
                             client_secret=self.client_secret,
                             user_agent=self.user_agent,
                             username=self.username,
                             password=self.password)

        self.webscrap_content()
        submissions = reddit.subreddit(self.subreddit).hot(limit=self.number_of_submissions)
        #self.read_comments_selenium(submissions)

    def convert_time(self):
        """Method to convert time readable in the Xpath in Selenium.

        Publication format in Reddit.
        if `self.time_ago` < 24 && > 1, publication date format in Reddit is hour (ex: a post published 5 hours ago will
            have a creation date of `5h` ago)
        if `self.time_ago` >= 24, publication date format in Reddit is day (ex: ex: a post published 28 hours ago will
            have a creation date of `1d` ago)

        We create `self.date_` with `self.buffer_date` values :
        -With Selenium, because of AJAX techniques the page  may load too slowly (with paramaters
            `self.pause_scroll_time` too low) not giving enough time to `EC.presence_of_element_located()` to find
            the element(s) in `self.scroll_to_value(self,driver)`
        -In the function `self.scroll_to_value(self,driver)` we may not find the expected `self.date_` value (ex:
            we are looking up for the posts during the last hour. It is possible that the latest posts we published 3
            hour ago). This is why we use a buffer.

        """

        now = datetime.now()  # get the current datetime, this is our starting point
        start_time = now - timedelta(hours=self.time_ago)  # datetime according to the number of the days ago we want

        #Write the day in Xpath format for reddit
        #write `self.date_` according to the format in Reddit. It depends on how far we webscrap data

        #create a left parenthesis, it's the first part of the string to pass in function
        #`EC.presence_of_element_located()`
        self.date_ = "("
        i = 0
        day_tempo = 1
        or_tempo = ' or '
        if self.time_ago < 24 :
            while i < self.buffer_date :
                if (i+1) == self.buffer_date :
                    or_tempo = ''
                if (self.time_ago + i) < 24 :
                    str_tempo = str(self.time_ago + i)
                    self.date_ += ''.join(['contains(text(),','"',str_tempo, 'h','"',')',or_tempo])
                    self.date__.append(str_tempo + 'h')
                else :
                    str_tempo = str(day_tempo)
                    self.date_ += ''.join(['contains(text(),','"',str_tempo, 'd','"',')',or_tempo])
                    self.date__.append(str(str_tempo + 'd'))

                    day_tempo +=1

                i+=1

        if self.time_ago >= 24:
            tempo_time = self.time_ago // 24
            while i < self.buffer_date:
                if (i+1) == self.buffer_date :
                    or_tempo = ''
                str_tempo = str(tempo_time + i)
                self.date_ += ''.join(['contains(text(),', '"', str_tempo, 'd', '"', ')', or_tempo])
                self.date__.append(str(str_tempo + 'd'))

                i+=1
        #right parenthisis in the function `EC.presence_of_element_located()`
        self.date_ += ")]"
        t = 5

    def accepted_replies(self):
        """ Method to make a list of the 'MoreComments' buttons we click on it. It depends on the number on replies
        `self.min_replies`. Ex: We may not want to click on all more comments button '1 more reply' as it takes times.
        """
        
        #We put in `self.allowed_replies_list` all the 'moreComments' we are allowed to click on
        i =0
        while i + self.min_replies < self.replies_buffer :
            if (i + self.min_replies) < 1000 :
                if i == 0 :
                    self.allowed_replies_list += ''.join([' and ((contains(.,', '"', str(i +self.min_replies),
                                                           ' more reply', '"))'])
                else :
                    self.allowed_replies_list += ''.join([' or (contains(.,', '"', str(i + self.min_replies),
                                                           ' more replies', '"))'])

            #separating thousand with comma. Ex : 7,019 more replies
            else :
                thousand_ = int((i + self.min_replies) // 1000)
                hundred_ = int(i + self.min_replies - thousand_*1000)

                if i == 0 :
                    self.allowed_replies_list += ''.join([' and ((contains(.,', '"',str(thousand_),',',str(hundred_),
                                                           ' more replies', '"))'])

                else :
                    self.allowed_replies_list += ''.join([' or (contains(.,', '"',str(thousand_),',',str(hundred_),
                                                           ' more replies', '"))'])
            i+=1

        self.allowed_replies_list += ')'


    def webscrap_content(self):
        """Method to web-scrap content on Reddit using Selenium
        """

        option = Options()
        #option.add_argument("--disable-infobars")
        #option.add_argument("start-maximized")
        #option.add_argument("--disable-extensions")

        # Pass the argument 1 to allow notifications and 2 to block them
        option.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })

        self.tempo_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/qezvzm/what_are_your_moves_tomorrow_october_25_2021/?sort=new'

        #driver = webdriver.Chrome(chrome_options=option, executable_path=self.driver_file_name)
        driver = webdriver.Firefox()
        driver.get(self.tempo_endpoint)
        time.sleep(2)

        reddit_dictionary = {}  # dictionary with information from twits

        self.scroll_to_value(driver)
        self.reddit_post = driver.find_elements_by_xpath(
            "//div[contains(@class,'{}')]".format(self.class_post))

        i = 0
        for reddit in self.reddit_post:
            #skip the stickied comment
            if i ==0 :
                i += 1
                continue
            i+=1

            #check if the post contains the stock (keywords) we are looking for
            for keyword in self.stock_keywords:
                if keyword in reddit.text:
                    break #not analyzi

            # remove all unescessary text (emoji, \n, other symbol like $)
            reddit_tempo = pm.text_cleanup(reddit.text)

            reddit_dictionary[self.reddit_columns[0]] = reddit_tempo

            self.reddit_result = self.reddit_result.append(reddit_dictionary, ignore_index=True)


        t= 5


    def scroll_to_value(self,driver):
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

        wait = WebDriverWait(driver, self.scroll_pause_time)
        element = None
        screen_height = driver.execute_script("return window.screen.height;") #return window screen height
        i = 1
        button_click_text =  '//div[contains(@class,self.class_more_comments) and (contains(@id,"moreComments"))' +\
                             self.allowed_replies_list + ']'
        is_clicking = False #not clicking on a button by default

        while not element:

            if is_clicking:
                button_click.click()
                is_clicking = False

            # go to section in window according to `i` and `screen_height`
            driver.execute_script(
                "window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))

            #return DOM body height
            scroll_height = driver.execute_script("return document.body.scrollHeight;")

            i += 1
            #check if we are a the end of the page
            if (screen_height) * i > scroll_height:
                print(f"WARNING : end of pages. Either `self.time_ago` {self.time_ago} is too large, either "
                               f"`self.scroll_pause_time` {self.scroll_pause_time} is too small or either the submissions"
                      f" is too 'young'")
                break


            #Check if there is a button 'MoreComments' and click on it to load more comments
            try:

                button_click = wait.until(EC.presence_of_element_located((By.XPATH, button_click_text)))
                is_clicking = True
                i-=1

            except:
                pass
                # we clicked on all the button that we want to click on


            #Trying to find the elements (@class `self.class_time` and the date `self.date_`)
            try:

                element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class,self.class_time)"
                            " and " +  self.date_)))

                self.reddit_time = driver.find_elements_by_xpath(
                    "//a[contains(@class,'{}')]".format(self.class_time))

                #here we need to loop through the element `self.class_time` to make sure that the `text()` founds
                #is in the xpath `self.class_time`, not in another xpath (in the post itself for example)
                element = None
                i = 0
                for reddit in self.reddit_time:
                    #skip the stickied comment
                    if i == 1 :
                        i += 1
                        continue
                    i += 1
                    for date_ in self.date__:
                        if date_ == reddit.text :
                            element = True
                            break
                    if element == True :
                        break

            except TimeoutException:
                pass

            if (i == 40):
                element = True

    def read_comments_selenium(self, submissions):
        """ This method allow to read first level comments (not sublevel comment) :
        https://praw.readthedocs.io/en/latest/code_overview/other/commentforest.html#praw.models.comment_forest.CommentForest
        It uses the Reddit API. It's the same thing as `self.read_comments()` except that it uses selenium to retrieve
        the data (instead of the Reddit API)

        1- We don't read the archived submissions as we don't they may be old and irrelevant (if not submission.archived)
        2- We discard the stickied comment as they are posted by the moderators and may be irrelevant. They are also
        even if we sort the posts by the newest one


        Using Selenium instead of the Reddit API because of Reddit API limitations (because ofmax 60 requests
        per hours, 100 comments max per requests, loading more comments which can be long
        `submission.comments.replace_more(limit = None)` and not top level comments in the submissions are loaded,
        even if this is what we want (bug in PRAW or need further testing?)
        """

        all_comments_body = []
        comment_time = []
        comment_score = []
        comment_number = 0
        new_comment = ""

        now = datetime.now()  # get the current datetime, this is our starting point
        # epoch unix time according how many hours (days) we want to fetch data
        start_time = (now - timedelta(hours=self.time_ago)).timestamp()

        for submission in submissions:
            comment_number = 0
            newest_comment_utc = None
            submission.comment_sort = self.sort_comments_method
            submission.comments.replace_more(limit=None)

            # check only if submission is not archived
            if not submission.archived:
                self.tempo_endpoint = self.reddit_endpoint + str(submission) + '/?sort=new'
                self.webscrap_content() #scraping content using Selenium

                # Iterate over all first level comments only (not sublevel comment)
                for comment in submission.comments:

                    # Check if current instance is `MoreComments`
                    if isinstance(comment, MoreComments):
                        continue

                    if not comment.stickied:
                        # Check if current comment is older than what we want to fetch (`self.time_ago`)
                        if comment.created_utc < start_time:
                            break
                        comment_number += 1

                        if newest_comment_utc and (comment.created_utc > newest_comment_utc):
                            raise Exception(
                                "current comment is older than previous one, which should not be the case")
                        newest_comment_utc = comment.created_utc

                        for keyword in self.stock_keywords:
                            if keyword in comment.body:
                                new_comment = pm.text_cleanup(comment.body)
                                all_comments_body.append(new_comment)
                                comment_time.append(comment.created_utc)
                                comment_score.append(comment.score)

        self.reddit_result[self.reddit_columns[0]] = all_comments_body
        self.reddit_result[self.reddit_columns[1]] = comment_time
        self.reddit_result[self.reddit_columns[2]] = comment_score


    def read_comments(self,submissions):
        """ This method allow to read first level comments (not sublevel comment) :
        https://praw.readthedocs.io/en/latest/code_overview/other/commentforest.html#praw.models.comment_forest.CommentForest
        It uses the Reddit API

        1- We don't read the archived submissions as we don't they may be old and irrelevant (if not submission.archived)
        2- We discard the stickied comment as they are posted by the moderators and may be irrelevant. They are also
        even if we sort the posts by the newest one
        """

        all_comments_body = []
        comment_time = []
        comment_score = []
        comment_number = 0
        new_comment = ""

        now = datetime.now()  # get the current datetime, this is our starting point
        # epoch unix time according how many hours (days) we want to fetch data
        start_time = (now - timedelta(hours=self.time_ago)).timestamp()


        for submission in submissions:
            comment_number = 0
            newest_comment_utc = None
            submission.comment_sort = self.sort_comments_method
            submission.comments.replace_more(limit=None)

            #check only if submission is not archived
            if not submission.archived :

                #Iterate over all first level comments only (not sublevel comment)
                for comment in submission.comments:

                    #Check if current instance is `MoreComments`
                    if isinstance(comment, MoreComments):
                        continue

                    #don't take the stickied comment as this is post by
                    if not comment.stickied:
                        #Check if current comment is older than what we want to fetch (`self.time_ago`)
                        if comment.created_utc < start_time:
                            break
                        comment_number += 1

                        if newest_comment_utc and (comment.created_utc > newest_comment_utc) :
                            raise Exception("current comment is older than previous one, which should not be the case")
                        newest_comment_utc = comment.created_utc

                        for keyword in self.stock_keywords:
                            if keyword in comment.body:
                                new_comment = pm.text_cleanup(comment.body)
                                all_comments_body.append(new_comment)
                                comment_time.append(comment.created_utc)
                                comment_score.append(comment.score)

        self.reddit_result[self.reddit_columns[0]] = all_comments_body
        self.reddit_result[self.reddit_columns[1]] = comment_time
        self.reddit_result[self.reddit_columns[2]] = comment_score