import os
import json
import datetime
import sys
import time

# import tweepy
import requests
from dotenv import load_dotenv

load_dotenv()
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

SAFE_TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S-%f"


def create_stats_file(filepath, stats_data):
    with open(filepath, "w") as fout:
        json.dump(stats_data, fout, indent=4)


def update_data_file(filepath, data):
    with open(filepath, "a") as fout:
        if isinstance(data, list):
            for item in data:
                json.dump(item, fout)
                fout.write("\n")
        else:
            json.dump(data, fout)
            fout.write("\n")


def get_total_hours(start_time, end_time):
    return round((end_time - start_time).total_seconds() / 3600, 2)


def search_recent_tweets(query, max_results=10, next_token=None):
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": max_results,
        "next_token": next_token,
    }
    response = requests.get(url, headers=headers, params=params)
    return response


def main(duration_hours=24, query="#example", data_dir="../../data"):

    # Will not use because it returns 429 often compared to simple requests library
    # api = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(hours=duration_hours)

    start_time_label = start_time.strftime(SAFE_TIMESTAMP_FORMAT)
    data_filename = f"twitter-UGC-question-19-data-{start_time_label}"
    stats_filename = f"twitter-UGC-question-19-stats-{start_time_label}"

    total_request_made = 0
    total_collected_data = 0
    next_token = None

    while datetime.datetime.now() < end_time:
        # DEVELOP UGC OC19 HERE

        response = search_recent_tweets(
            query=query, max_results=10, next_token=None
        )
        if response.status_code == 429:
            print(f"Rate limit exceeded")
            print("Sleeping for 15 minutes")
            time.sleep(15 * 60)
            continue
        elif response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            print("Cannot continuously acquire data. Exiting.")
            break
        elif "data" not in response.json():
            print("No data found.")
            print(response.json())
            print("Cannot continuously acquire data. Exiting.")
            break

        next_token = response.json().get("meta", {}).get("next_token", None)
        print(f"Next token: {next_token}")
        data = response.json().get("data", [])
        total_request_made += 1
        total_collected_data += len(data)
        update_data_file(f"{data_dir}/{data_filename}", data)

    actual_end_time = datetime.datetime.now()

    acquisition_stats = {
        "start_time": start_time.isoformat(),
        "end_time": actual_end_time,
        "total_acquision_time_hour": get_total_hours(start_time, actual_end_time),
        "total_requests_made": total_request_made,
        "total_data_collected": total_collected_data,
    }
    create_stats_file(f"{data_dir}/{stats_filename}", acquisition_stats)


if __name__ == "__main__":
    # Get parameters from command line arguments
    # ATTENTION: THIS IS NOT ROBUST. FOR DEMONSTRATION PURPOSES ONLY.
    duration_hours = int(sys.argv[1])
    query = sys.argv[2]
    data_dir = sys.argv[3] if len(sys.argv) > 3 else "../../data"
    main(duration_hours=duration_hours, query=query, data_dir=data_dir)
