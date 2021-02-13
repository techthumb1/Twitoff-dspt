"""Retrieve tweetes and users then create embeddings and populate DB"""

from os import getenv
import tweepy
import spacy
from .models import DB, Tweet, User

TWITTER_API_KEY = getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = getenv("TWITTER_API_KEY_SECRET")
TWITTER_AUTH = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
TWITTER = tweepy.API(TWITTER_AUTH)

# nlp model
# Use nlp spacy model sm
nlp = spacy.load('en_core_web_sm')


def vectorize_tweet(tweet_text):
    return nlp(tweet_text).vector


def add_or_update_user(username):
    try:
        # grabs user from twitter DB
        twitter_user = TWITTER.get_user(username)
        # adds or updates user
        db_user = (User.query.get(twitter_user.id)) or User(
            id=twitter_user.id, name=username)
        DB.session.add(db_user)

        # grabs tweets from twitter_user
        tweets = twitter_user.timeline(
            count=200, exclude_replies=True, include_rts=False,
            tweet_mode="extended", since_id=db_user.newest_tweet_id
        )

        # adds newest tweet to db_user.newest_tweet_id
        if tweets:
            db_user.newest_tweet_id = tweets[0].id

        for tweet in tweets:
            # stores numerical representations
            vectorized_tweet = vectorize_tweet(tweet.full_text)
            db_tweet = Tweet(id=tweet.id, text=tweet.full_text,
                             vect=vectorized_tweet)
            db_user.tweets.append(db_tweet)
            DB.session.add(db_tweet)

    except Exception as e:
        # prints error to user and raises throughout app
        print('Error processing{}: {}'.format(username, e))
        raise e

    # commits changes after try has completed
    else:
        DB.session.commit()


def update_all_users():
    """Update all Tweets for all Users in the User table."""
    for user in User.query.all():
        add_or_update_user(user.name)