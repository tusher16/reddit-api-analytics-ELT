import configparser
import datetime
import pandas as pd
import pathlib
import praw
import sys
import numpy as np
import logging
from validation import validate_input

"""
Part of Airflow DAG. Takes in one command line argument of format YYYYMMDD. 
Script will connect to Reddit API and extract top posts from past day
with no limit. For a small subreddit like Data Engineering, this should extract all posts
from the past 24 hours.
"""

# Read Configuration File
parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
config_file = "configuration.conf"
parser.read(f"{script_path}/{config_file}")

# Configuration Variables
SECRET = parser.get("reddit_config", "secret")
CLIENT_ID = parser.get("reddit_config", "client_id")

# Options for extracting data from PRAW
SUBREDDIT = "datascience"
TIME_FILTER = "day"
LIMIT = None

# Fields that will be extracted from Reddit.
# Check PRAW documentation for additional fields.
# NOTE: if you change these, you'll need to update the create table
# sql query in the upload_aws_redshift.py file
POST_FIELDS = (
    "id",
    "title",
    "score",
    "num_comments",
    "author",
    "created_utc",
    "url",
    "upvote_ratio",
    "over_18",
    "edited",
    "spoiler",
    "stickied",
)

# Use command line argument as output file
# name and also store as column value
try:
    output_name = sys.argv[1]
except Exception as e:
    print(f"Error with file input. Error {e}")
    sys.exit(1)
date_dag_run = datetime.datetime.strptime(output_name, "%Y%m%d")


def main():
    """
     Extract Reddit data and load to CSV. This is the main function of the script. It takes input from command line
    """
    validate_input(output_name)
    reddit_instance = api_connect()
    subreddit_posts_object = subreddit_posts(reddit_instance)
    extracted_data = extract_data(subreddit_posts_object)
    transformed_data = transform_basic(extracted_data)
    load_to_csv(transformed_data)

def api_connect():
    """
     Connect to Reddit API. Retry up to 3 times if connection fails. This is useful for unit testing
     
     
     @return Instance of praw.
    """
    """Connect to Reddit API"""
    retries = 3
    delay = 1
    # Get Reddit instance from Reddit API.
    for i in range(retries):
        try:
            instance = praw.Reddit(
                client_id=CLIENT_ID, client_secret=SECRET, user_agent="My User Agent"
            )
            return instance
        except Exception as e:
            logging.error(f"Failed to connect to Reddit API. Error: {e}")


def subreddit_posts(reddit_instance):
    """
     Get posts for subreddit. This function is used to get posts for subreddit. It will return a list of posts object which is of type praw. Post.
     
     @param reddit_instance - Reddit instance for which posts will be retrieved.
     
     @return Posts object for subreddit. Example :. from praw import posts Posts object = posts. subreddit_posts
    """
    """Create posts object for Reddit instance"""
    try:
        subreddit = reddit_instance.subreddit(SUBREDDIT)
        posts = subreddit.top(time_filter=TIME_FILTER, limit=LIMIT)
        return posts
    except praw.exceptions.APIException as api_error:
        # Handle specific API exceptions
        print(f"API Exception: {api_error.message}")
    except prawcore.exceptions.ServerError as server_error:
        # Handle server errors
        print(f"Server Error: {server_error}")
    except Exception as e:
        # Handle all other exceptions
        print(f"Unexpected Exception: {e}")
    sys.exit(1)


def extract_data(posts):
    """
     Extracts data from a list of Posts to a Pandas DataFrame. This function is used to extract data from a list of Posts that are to be saved to a Posts database
     
     @param posts - List of Posts to be extracted
     
     @return A Pandas DataFrame with the extracted data from the Posts to be saved to a Posts database. The columns correspond to the post
    """
    """Extract Data to Pandas DataFrame object"""
    list_of_items = []
    try:
        # Add a dictionary of submission variables to the list of items in the list of submissions.
        for submission in posts:
            to_dict = vars(submission)
            sub_dict = {field: to_dict[field] for field in POST_FIELDS}
            list_of_items.append(sub_dict)
        extracted_data_df = pd.DataFrame(list_of_items)
    except KeyError as key_error:
        # Handle key errors (e.g., if a field is missing from the post)
        print(f"Key Error: {key_error}")
    except Exception as e:
        # Handle all other exceptions
        print(f"Unexpected Exception: {e}")
        sys.exit(1)

    return extracted_data_df


def transform_basic(df):
    """
     Basic transformation of data. It is used to refactored and reorganize data to be compatible with old and new versions
     
     @param df - Dataframe to be transformed.
     
     @return Dataframe with transformed data in columns " created_utc " " over_18 " " edited "
    """
    """Some basic transformation of data. To be refactored at a later point."""

    # Convert epoch to UTC
    df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")
    # Fields don't appear to return as booleans (e.g. False or Epoch time). Needs further investigation but forcing as False or True for now.
    # TODO: Remove all but the edited line, as not necessary. For edited line, rather than force as boolean, keep date-time of last
    # edit and set all else to None.
    df["over_18"] = np.where(
        (df["over_18"] == "False") | (df["over_18"] == False), False, True
    ).astype(bool)
    df["edited"] = np.where(
        (df["edited"] == "False") | (df["edited"] == False), False, True
    ).astype(bool)
    df["spoiler"] = np.where(
        (df["spoiler"] == "False") | (df["spoiler"] == False), False, True
    ).astype(bool)
    df["stickied"] = np.where(
        (df["stickied"] == "False") | (df["stickied"] == False), False, True
    ).astype(bool)
   
    return df



def load_to_csv(extracted_data_df):
    """
     Save extracted data to CSV file in / tmp folder. This is a convenience function to be used in unit tests
     
     @param extracted_data_df - dataframe with extracted data
    """
    """Save extracted data to CSV file in /tmp folder"""
    extracted_data_df.to_csv(f"/tmp/{output_name}.csv", index=False)


# main function for the main module
if __name__ == "__main__":
    main()