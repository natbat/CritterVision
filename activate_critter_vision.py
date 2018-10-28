import json
import time
import os
import sys
import twitter
import requests
import hashlib
import shutil
import random
from dateutil import parser

BATCH_SIZE = 20
TARGET_USER = "drmichellelarue"
TARGET_HASHTAG = "cougarornot"
num_pages_to_fetch = 1


def get_tweets(
    api,
    user=TARGET_USER,
    num_pages_to_fetch=1,
    count=BATCH_SIZE,
    exclude_replies=True,
    include_rts=False,
):
    # Fetch BATCH_SIZE recent tweets from users we follow
    max_id = None
    tweets = []

    for i in range(num_pages_to_fetch):

        print("max_id: %r" % max_id)

        tweets.extend(
            api.GetUserTimeline(
                screen_name=user,
                exclude_replies=exclude_replies,
                include_rts=include_rts,
                max_id=max_id,
                count=count,
            )
        )
        # (user_id=None, screen_name=None, since_id=None, max_id=None, count=None,
        # include_rts=True, trim_user=False, exclude_replies=False)

        max_id = min([tweet.id for tweet in tweets]) - 1

    print("FETCHED %d tweets" % len(tweets))
    print()
    return tweets


def tweet_matches_rules(full_text, hashtag=TARGET_HASHTAG):

    # Extract information about the tweet
    full_text = full_text.lower()
    hashtag = hashtag.lower()

    if ("#" + hashtag) in full_text:
        return True

    return False


def find_correct_tweets(tweets):

    correct_tweets = []

    for tweet in tweets:
        # For every tweet, see if it matches the rule

        if tweet_matches_rules(tweet.full_text):
            correct_tweets.append(tweet)
        else:
            pass

    return correct_tweets


def getPhotoURL(tweet):

    if not tweet.media:
        return ""

    media_url = tweet.media[0].media_url_https
    return media_url


def build_tweet(predictions):

    adjectives = [
        "beautiful",
        "pretty",
        "magnificent",
        "delightful",
        "suprised",
        "lovely",
        "nice",
        "glossy",
        "fuzzy",
    ]

    names = {
        "Bobcat": "Bobcat",
        "Domestic-Cat": "House Cat",
        "Mountain-Lion": "Cougar",
        "Eastern-Bobcat": "Eastern Bobcat",
        "North-American-Mountain-Lion": "North American Cougar",
        "Western-Bobcat": "Western Bobcat",
        "Canada-Lynx": "Canada Lynx",
        "Jaguar": "Jaguar",
        "Central-American-Ocelot": "Central American Ocelot",
        "Ocelot": "Ocelot",
    }

    best = predictions[0]
    alternatives = predictions[1:4]

    tweet_string = "@{username} I think this is a photo of a {adjective} {name} ({score:.3f}) #CougarOrNot \n\nAlternatively it could be: ".format(
        username=TARGET_USER,
        adjective=random.choice(adjectives),
        name=names[best[0]],
        score=best[1],
    )

    others = [
        "{} ({:.3f})".format(names[alternative[0]], alternative[1])
        for alternative in alternatives
    ]

    tweet_string += ", ".join(others)

    return tweet_string


def reply_to_tweets(target_tweets, my_tweets):
    tweetIDs_replied_to = {
        t.in_reply_to_status_id
        for t in my_tweets
        if t.in_reply_to_status_id is not None
    }

    for tweet in target_tweets:
        print("------")
        if tweet.id in tweetIDs_replied_to:
            print("I already replied to it")
        else:
            print("I have not replied to it")

            url = getPhotoURL(tweet)

            if url:
                predictions = requests.get(
                    "https://cougar-or-not.now.sh/classify-url", params={"url": url}
                ).json()["predictions"]

                print(url)
                print(predictions)

                tweet_text = build_tweet(predictions)
                print(tweet_text, len(tweet_text))

                api.PostUpdate(status=tweet_text, in_reply_to_status_id=tweet.id_str)


if __name__ == "__main__":

    api = twitter.Api(
        tweet_mode="extended",
        consumer_key=os.environ["CONSUMER_KEY"],
        consumer_secret=os.environ["CONSUMER_SECRET"],
        access_token_key=os.environ["ACCESS_TOKEN_KEY"],
        access_token_secret=os.environ["ACCESS_TOKEN_SECRET"],
    )

    target_tweets = find_correct_tweets(get_tweets(api, num_pages_to_fetch=5))
    my_tweets = get_tweets(api, user="critter_vision", exclude_replies=False)

    reply_to_tweets(target_tweets, my_tweets)
