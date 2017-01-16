from twitter_follow_bot import auto_fav, auto_follow_followers_for_user, auto_unfollow_nonfollowers, auto_follow
import time


keywords = {"#startupsandiego", "#sandiegotech", "#startupsd", "#sdtech"};
count = 3;
sleep_time = 60;

while (1):
	time.sleep(sleep_time)
	for key in keywords:
		print "## Favoriting: " + key + "##"
		auto_fav(key, count)
