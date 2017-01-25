# -*- coding: utf-8 -*-

"""
Copyright 2014 Randal S. Olson

This file is part of the Twitter Follow Bot library.

The Twitter Follow Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any
later version.

The Twitter Follow Bot library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with the Twitter
Follow Bot library. If not, see http://www.gnu.org/licenses/.

Code only slightly modified by Programming for Marketers to allow for separate variable 
storage.
"""

from twitter import Twitter, OAuth, TwitterHTTPError
import os
from twitter_info import *

# put the full path and file name of the file you want to store your "already followed"
# list in
ALREADY_FOLLOWED_FILE = "already-followed.csv"
ALREADY_FAV_FILE = "already-fav.csv"
IGNORE_USERS_FILE = "ignore-users.csv"

t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
            CONSUMER_KEY, CONSUMER_SECRET))


def search_tweets(q, count=100, result_type="recent"):
    """
        Returns a list of tweets matching a certain phrase (hashtag, word, etc.)
    """

    return t.search.tweets(q=q, result_type=result_type, count=count)


def auto_fav(q, count=100, result_type="recent"):
    """
        Favorites tweets that match a certain phrase (hashtag, word, etc.)
    """

    all_favs = get_already_favs()
    ignored_users = get_ignore_users()
    
    f_out = open(ALREADY_FAV_FILE, 'a')

    result = search_tweets(q, count, result_type)


    for tweet in result["statuses"]:
        try:
            # don't favorite your own tweets
            if tweet["user"]["screen_name"] == TWITTER_HANDLE:
                continue

            if (was_favorited(tweet["id"], all_favs)):
                continue

            if in_numeric_list(tweet["user"]["id"], ignored_users):
                continue

            add_favorite_to_file(tweet["id"], f_out)

            result = t.favorites.create(_id=tweet["id"])
            print("favorited: %s" % (result["text"].encode("utf-8")))

        # when you have already favorited a tweet, this error is thrown
        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))
            print("error in user:" tweet["user"]["screen_name"])
            print("error in tweet id:" tweet["id"])

    f_out.close()

def get_already_favs():
   return get_list_from_file(ALREADY_FAV_FILE)

def get_ignore_users():
    return get_list_from_file(IGNORE_USERS_FILE)

def get_list_from_file(path):

    list = []

     # Read all favs file
    if not os.path.isfile(path):
        with open(path, "w") as out_file:
            out_file.write("")
    with open(path, 'r') as in_file:
        for line in in_file:
            all_favs.append(int(line))

    return list

def auto_rt(q, count=100, result_type="recent"):
    """
        Retweets tweets that match a certain phrase (hashtag, word, etc.)
    """

    result = search_tweets(q, count, result_type)

    for tweet in result["statuses"]:
        try:
            # don't retweet your own tweets
            if tweet["user"]["screen_name"] == TWITTER_HANDLE:
                continue

            result = t.statuses.retweet(id=tweet["id"])
            print("retweeted: %s" % (result["text"].encode("utf-8")))

        # when you have already retweeted a tweet, this error is thrown
        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))


def get_do_not_follow_list():
    """
        Returns list of users the bot has already followed.
    """

    # make sure the "already followed" file exists
    if not os.path.isfile(ALREADY_FOLLOWED_FILE):
        with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
            out_file.write("")

        # read in the list of user IDs that the bot has already followed in the
        # past
    do_not_follow = set()
    dnf_list = []
    with open(ALREADY_FOLLOWED_FILE) as in_file:
        for line in in_file:
            dnf_list.append(int(line))

    do_not_follow.update(set(dnf_list))
    del dnf_list

    return do_not_follow


def auto_follow(q, count=100, result_type="recent"):
    """
        Follows anyone who tweets about a specific phrase (hashtag, word, etc.)
    """

    result = search_tweets(q, count, result_type)
    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    do_not_follow = get_do_not_follow_list()

    for tweet in result["statuses"]:
        try:
            if (tweet["user"]["screen_name"] != TWITTER_HANDLE and
                    tweet["user"]["id"] not in following and
                    tweet["user"]["id"] not in do_not_follow):

                t.friendships.create(user_id=tweet["user"]["id"], follow=False)
                following.update(set([tweet["user"]["id"]]))

                print("followed %s" % (tweet["user"]["screen_name"]))

        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))

            # quit on error unless it's because someone blocked me
            if "blocked" not in str(e).lower():
                quit()


def auto_follow_followers_for_user(user_screen_name, count=100):
    """
        Follows the followers of a user
    """
    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    followers_for_user = set(t.followers.ids(screen_name=user_screen_name)["ids"][:count])
    do_not_follow = get_do_not_follow_list()
    
    for user_id in followers_for_user:
        try:
            if (user_id not in following and 
                user_id not in do_not_follow):

                t.friendships.create(user_id=user_id, follow=False)
                print("followed %s" % user_id)

        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))

def auto_follow_followers():
    """
        Follows back everyone who's followed you
    """

    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    followers = set(t.followers.ids(screen_name=TWITTER_HANDLE)["ids"])

    not_following_back = followers - following

    for user_id in not_following_back:
        try:
            t.friendships.create(user_id=user_id, follow=False)
        except Exception as e:
            print("error: %s" % (str(e)))


def auto_unfollow_nonfollowers():
    """
        Unfollows everyone who hasn't followed you back
    """

    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    followers = set(t.followers.ids(screen_name=TWITTER_HANDLE)["ids"])

    # put user IDs here that you want to keep following even if they don't
    # follow you back
    users_keep_following = set([])

    not_following_back = following - followers

    # make sure the "already followed" file exists
    if not os.path.isfile(ALREADY_FOLLOWED_FILE):
        with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
            out_file.write("")

    # update the "already followed" file with users who didn't follow back
    already_followed = set(not_following_back)
    af_list = []
    with open(ALREADY_FOLLOWED_FILE) as in_file:
        for line in in_file:
            af_list.append(int(line))

    already_followed.update(set(af_list))
    del af_list

    with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
        for val in already_followed:
            out_file.write(str(val) + "\n")

    for user_id in not_following_back:
        if user_id not in users_keep_following:
            t.friendships.destroy(user_id=user_id)
            print("unfollowed %d" % (user_id))

def set_already_followed_file():

    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])

    # make sure the "already followed" file exists
    if not os.path.isfile(ALREADY_FOLLOWED_FILE):
        with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
            out_file.write("")

    # update the "already followed" file with users who didn't follow back
    already_followed = set(following)
    af_list = []
    with open(ALREADY_FOLLOWED_FILE) as in_file:
        for line in in_file:
            af_list.append(int(line))

    already_followed.update(set(af_list))
    del af_list

    with open(ALREADY_FOLLOWED_FILE, "a") as out_file:
        for val in already_followed:
            out_file.write(str(val) + "\n")

def was_favorited(tweet_id, all_tweets):
    return in_numeric_list(tweet_id, all_tweets)

def in_numeric_list(id, list):
    for line in list:
        if id == int(line):
            return True

    return False


def add_favorite_to_file(tweet_id, out_file):
    out_file.write(str(tweet_id) + "\n")



   

def auto_mute_following():
    """
        Mutes everyone that you are following
    """
    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    muted = set(t.mutes.users.ids(screen_name=TWITTER_HANDLE)["ids"])

    not_muted = following - muted

    # put user IDs of people you do not want to mute here
    users_keep_unmuted = set([])
            
    # mute all        
    for user_id in not_muted:
        if user_id not in users_keep_unmuted:
            t.mutes.users.create(user_id=user_id)
            print("muted %d" % (user_id))


def auto_unmute():
    """
        Unmutes everyone that you have muted
    """
    muted = set(t.mutes.users.ids(screen_name=TWITTER_HANDLE)["ids"])

    # put user IDs of people you want to remain muted here
    users_keep_muted = set([])
            
    # mute all        
    for user_id in muted:
        if user_id not in users_keep_muted:
            t.mutes.users.destroy(user_id=user_id)
            print("unmuted %d" % (user_id))
