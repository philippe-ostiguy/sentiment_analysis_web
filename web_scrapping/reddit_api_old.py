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
from webdriver_manager.firefox import GeckoDriverManager

"""Module to webscrap data from reddit api. It's the 'old' one as we use time to decide until when we webscrap data.
It stops webscrapping when it sees the 'date' in a comment. Ex: if we want the 3 previous days of data (`self.time_ago`), 
il will stop webscrapping in the posts when the date of a comment is '3d'.

The issue with that technic is that event if we filter the comments from the newest one, when we load more comments
(clicking on button 'more replies' at the button of the page or object called 'MoreComments' when we webscrap), the new
loaded comment won't be sorted by the newest common. 

"""

class RedditApi_():
    """Class to make requests to the Reddit API. Thing to know :
    -Max 60 requests per minute : https://www.reddit.com/r/redditdev/comments/gz01fo/data_rate_limit_more_than_60_requests_per_minute/
    -Max 100 comments per request. The Package PRAW (to make API requests to Reddit) will stop making API calls
    if there is more than 60 requests per minute made. It will resume doign API calls by itself :
    https://www.reddit.com/r/redditdev/comments/l4uty1/what_is_the_max_number_of_comments_im_able_to/ +
    https://praw.readthedocs.io/en/latest/code_overview/other/listinggenerator.html?highlight=1000
    -`submission.comments.replace_more(limit=None)` retrieve additional comments (with the button in the UI
    'load comments' or 'more replies') up to 100 commetns at a time
    - This


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
            buffer (number) to fetch the dates we want. Ex :  If the buffer is 3, and `self.time_ago` is 5 hours,
            it will also stop fetching the data if it sees 6 hours or 7 hours in the post and set the value
            `self.date__` accordingly
        `self.date__` : str
            list of date we try to find in a post which will make the fetch stops if one of the date is found.
            The lenght of the list depends on `self.buffer_time_size` and is set in function `self.set_buffer_time_size`
        """

        self.username = config('USERNAME_REDDIT')
        self.password = config('PASSWORD_REDDIT')
        self.client_id =config('CLIENT_ID_REDDIT')
        self.client_secret=config('CLIENT_SECRET_REDDIT')
        self.user_agent=config('USER_AGENT_REDDIT')

        self.subreddit = 'wallstreetbets'
        self.stock_keywords = ['TSLA','Tesla']
        self.time_ago  = 48
        self.sort_comments_method = "new"
        self.date_ = ""

        self.reddit_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/'
        self.tempo_endpoint = '' #Temporary endpoint - we add the ticker we want to webscrap at the end of
                                 #self.stock_endpoint
        self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chromedriver')
        #self.driver_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'geckodriver')
        self.scroll_pause_time = 1
        self.class_time = '_3yx4Dn0W3Yunucf5sVJeFU' #time
        self.class_time_whole = '_1a_HxF03jCyxnx706hQmJR' #class time with more details
        self.class_whole_post = '_3tw__eCCe7j-epNCKGXUKk' #whole post
        self.class_more_comments='_3sf33-9rVAO_v4y0pIW_CH'
        self.class_post = '_3cjCphgls6DH-irkVaA0GM' #post
        self.class_submission_time = '_3jOxDPIQ0KaOWpzvSQo-1s'
        self.min_replies = 100
        self.min_reply_list = [] #associated list with the `self.min_replies` attribute
        self.rejected_replies_list = "" #list of MoreComments buttons we don't click on it. It depends of
                                        #`self.min_replies`
        self.buffer_time_size = 10
        self.date__ = ""

        self.reddit_result = pd.DataFrame()
        self.reddit_columns = ['comment', 'time_published','comment_score']
        self.number_of_submissions = 5

    def __call__(self):

        self.convert_time()
        self.set_buffer_time_size()
        self.rejected_replies()
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
        """

        if self.time_ago  < 24 :
            str_tempo = str(self.time_ago)
            self.date_ = ''.join([str_tempo, 'h'])
        else :
            str_tempo = str(self.time_ago//24)
            self.date_ = ''.join([str_tempo, 'd'])

    def set_buffer_time_size(self):
        """Method that set the variable `self.date__` depending on the size of the buffer `self.buffer_time_size` and 
        how far we need data `self.time_ago`. It will stop fetching in the submission if a post contains a date within
        the list `self.date__`
         """
        
        value_ = self.time_ago
        i = 1
        j= 1

        while i < self.buffer_time_size :
            if (i - 1 + self.time_ago) < 24:
                str_tempo = str(i -1 + self.time_ago)
                if i == 1:
                    self.date__ += "".join([' ./a/text() = ','"',str_tempo,'h"'])
                else :
                    self.date__ += "".join([' or ./a/text() = ', '"', str_tempo, 'h"'])

            else :

                str_tempo = str((i - 1 + j -1 + self.time_ago)//24)
                j +=24 #24 hours in 1 day
                if i == 1:
                    self.date__ += "".join([' ./a/text() = ','"',str_tempo,'d"'])
                else :
                    self.date__ += "".join([' or ./a/text() = ', '"', str_tempo, 'd"'])
            i+=1

    def rejected_replies(self):
        """ Method to make a list of the 'MoreComments' buttons we don't click on. It depends on the number on replies
        `self.min_replies`. Ex: We may not want to click on all more comments button '1 more reply' as it takes times.
        """
        
        #We put in `self.rejected_replies_list` all the 'moreComments' we are not allowed to click on
        i =1

        while i < self.min_replies:
            if i == 1 :
                self.rejected_replies_list += ''.join([' and not(./div/p/text() = ','"',str(i), ' more reply','")'])
            else :
                self.rejected_replies_list += ''.join([' and not(./div/p/text() = ', '"', str(i), ' more replies', '")'])

            i+=1


    def webscrap_content(self):
        """Method to web-scrap content on Reddit using Selenium
        """

        #Options for Chrome Driver
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")
        # Pass the argument 1 to allow notifications and 2 to block them
        option.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })

        self.tempo_endpoint = 'https://www.reddit.com/r/wallstreetbets/comments/qnjay6/weekend_discussion_thread_for_the_weekend_of/?sort=new'

        #driver = webdriver.Chrome(chrome_options=option, executable_path=self.driver_file_name)
        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en-US, en')
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),firefox_profile=profile)


        driver.get(self.tempo_endpoint)
        time.sleep(2)

        reddit_dictionary = {}  # dictionary with information from twits

        start_time = time.time()
        self.scroll_to_value(driver)
        end_time = time.time()
        difference = end_time - start_time
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
                    break #not analyzing the same post twic (in case we have more than 1 keyword)

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
        button_click_text = '//div[@class = "{}" and (contains(@id,"moreComments"))'.format(self.class_more_comments) \
                            + self.rejected_replies_list

        date_searching =  '//span[@class = "{}" and ./a[contains(@id, "CommentTopMeta")] and ({}) and not ' \
                          '(./span/text() = "Stickied comment")]'.format(self.class_time_whole,self.date__)

        is_clicking = False #not clicking on a button by default

        while not element:

            # go to section in window according to `i` and `screen_height`
            driver.execute_script(
                "window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
            #return DOM body height
            scroll_height = driver.execute_script("return document.body.scrollHeight;")

            i +=1
            is_clicking = False

            #check if we are a the end of the page
            if (screen_height) * i > scroll_height:
                #the scrolling may go to quickly and arrives at the end of the page prematurely
                try :
                    button_click = wait.until(EC.presence_of_element_located((By.XPATH, button_click_text + ']')))
                    button_click.click()

                except:
                    print(f"WARNING : end of pages. Either `self.time_ago` {self.time_ago} is too large, either "
                                   f"`self.scroll_pause_time` {self.scroll_pause_time} is too small or either the submissions"
                          f" is too 'young'")
                    break

            #get the time the submission what created
            try:
                creation_time_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@class = '{}' and "
                                   "@data-click-id = 'timestamp']".format(self.class_submission_time))))


            except:
                raise Exception(f"Not able to find the time the submission was published. Maybe a problem with waiting"
                                f"value {self.scroll_pause_time} or with the class to get the time the submission was "
                               f"created {self.class_submission_time}")

            #element exists
            if creation_time_element :
                is_older = self.compare_time(creation_time_element)

            #try to find posts that were published `self.time_ago` only if the submission was created before that.
            #Otherwise, searching for the element is time consuming (and slow down the process a lot).
            if is_older :

                #Trying to find the elements (@class `self.class_time` and the date `self.date_`.).
                # We skip the stickied comment and search for `@id` 'CommentTopMeta' contained in comments
                try:

                    element = wait.until(EC.presence_of_element_located((By.XPATH,date_searching )))
                    break

                except TimeoutException:
                    pass

            #Check if there is a button 'MoreComments' and click on it to load more comments
            try:
                button_click = wait.until(EC.presence_of_element_located((By.XPATH, button_click_text + ']')))
                button_click.click()
                is_clicking = True

            except:
                pass

    def compare_time(self,element):
        """ Method that return True if the submission was published before `self.time_ago` and False otherwise

        Ex : the submission was created '2 days ago', and we are looking for posts that were published 1 day ago, then
        it returns True"""

        time_format = element.text.split(' ')[1]
        #check if it is 'day ago' or 'hours ago' to get 'hours ago' at the end
        time_number = int(element.text.split(' ')[0])

        if (time_format == 'day' or time_format == 'days'):
            if ((24*time_number) >= self.time_ago):
                return True
            else :
                return False

        else :
            if time_number >= self.time_ago :
                return True
            else :
                return False



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