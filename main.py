import requests
import feedparser
from datetime import datetime

from openai import OpenAI

import tweepy

import mysql.connector
from mysql.connector import Error

from dotenv import load_dotenv
import os

load_dotenv()

consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

openai_api_key = os.getenv("OPENAI_API_KEY")

mySQL_database = os.getenv("MYSQL_DATABASE")
mySQL_password = os.getenv("MYSQL_PASSWORD")
mySQL_host = os.getenv("MYSQL_HOST")
mySQL_user = os.getenv("MYSQL_USER")


client_twitter = tweepy.Client(consumer_key= consumer_key,
                    consumer_secret=consumer_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret)

def arXiv_scrapper():
    # arXiv API endpoint
    ARXIV_API_URL = "http://export.arxiv.org/api/query?"

    # Parameters for the API query  
    query_params = {
        'search_query': 'cat:cs.LG',  # Search in the Machine Learning category, change as needed
        'start': 0,  # Starting point of the results
        'max_results': 1,  # Number of results to return, adjust as needed
    }

    # Make the request to arXiv API
    response = requests.get(ARXIV_API_URL, params=query_params)

    # Parse the response using feedparser
    feed = feedparser.parse(response.content)

    return feed

# Connecting the data to the database in MySQL
def insert_article(title, author, abstract, publication_date, url, keywords, summary):
    try:
        conn = mysql.connector.connect(
            host=mySQL_host,
            user=mySQL_user,
            password=mySQL_password,
            database=mySQL_database
        )
        cursor = conn.cursor()

        # Use the INSERT query as before, now publication_date is directly a string
        insert_query = """
        INSERT INTO papers (title, author, abstract, publication_date, url, keywords, summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (title, author, abstract, publication_date, url, keywords, summary))
        
        conn.commit()
    except Error as e:
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def generate_tweet(article):
    if article is None:
        return "No article found to tweet about."

    client = OpenAI(api_key=openai_api_key)


    # Define the initial content for the tweet
    initial_content = f"Create an engaging tweet presenting this research '{article['title']}' - {article['summary']} and provide the link to the article: {article['link']}, the twit should not exceed 280 characters"

    # Initialize tweet content
    tweet_content = ""

    # Attempt to generate a tweet within the length limit
    attempts = 0
    while len(tweet_content) > 280 or tweet_content == "":
        # Increase attempts count
        attempts += 1
        
        # If we've tried too many times, break to avoid an infinite loop
        if attempts > 5:
            return "Failed to generate a short enough tweet after several attempts."
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": initial_content,
                }
            ],
            model="gpt-3.5-turbo",
        )

        tweet_content = response.choices[0].message.content
        # Ensure the tweet is within the length limit
        if len(tweet_content) > 280:
            tweet_content = ""  # Reset tweet content and try again

    return tweet_content

def post_tweet(tweet_content):
    # Make sure to import and authenticate your Twitter client here
    response = client_twitter.create_tweet(text=tweet_content)
    print(f"Tweet posted: {response.data}")


def process_arxiv_feed(feed):
    # Extract and structure the data
    for entry in feed.entries:

        tweet_content = generate_tweet(entry)

        # Assuming there is a single URL per entry, and adjusting 'keywords' as needed
        url = [link.href for link in entry.links if link.rel == 'alternate'][0] if entry.links else None

        # Join authors by comma, you might need to adjust based on your schema
        authors = ', '.join(author.name for author in entry.authors)

        # Extract additional fields from the entry
        id = entry.id
        title = entry.title
        abstract = entry.summary
        publication_date = entry.published

        keywords = entry.get('tags', '')
        keywords = ', '.join([tag['term'] for tag in keywords]) if keywords else ''

        summary = tweet_content

        # Call your function to insert data
        insert_article(title, authors, abstract, publication_date, url, keywords, tweet_content)

feed = arXiv_scrapper()

articles = feed.entries

# article = fetch_article()

tweet_content = generate_tweet(articles[0])

process_arxiv_feed(feed)

post_tweet(tweet_content)