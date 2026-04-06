import os
import json
import datetime
import praw
from time import sleep
from dotenv import load_dotenv

load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USERAGENT = os.getenv("REDDIT_USERAGENT")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
FILEPATH = os.getenv("FILEPATH")

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


def main(duration_hours=24):

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USERAGENT,
    )
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(hours=duration_hours)
    print(start_time)
    print(end_time)

    data_dir = FILEPATH
    start_time_label = start_time.strftime(SAFE_TIMESTAMP_FORMAT)
    data_filename = f".br-reddit-UGC-question-19-data-{start_time_label}.jsonlines"
    stats_filename = f".br-reddit-UGC-question-19-stats-{start_time_label}.json"

    total_request_made = 0
    total_collected_data = 0
    data = []

    subreddit = reddit.subreddit("all")
    try:
        for submission in subreddit.stream.submissions():
            if datetime.datetime.now() > end_time:
                break
            print(submission.id)
            response = {
                "post_id": submission.id,
                "title": submission.title,
                "author": str(submission.author),
                "created": submission.created,
                "subreddit": submission.subreddit_name_prefixed,
                "permalink": submission.permalink,
            }
            data.append(response)
            sleep(0.5)
            total_request_made += 1
    except Exception as e:
        print(e)
    total_collected_data += len(data)
    update_data_file(f"{data_dir}/{data_filename}", data)

    actual_end_time = datetime.datetime.now()

    acquisition_stats = {
        "start_time": start_time.isoformat(),
        "end_time": actual_end_time.isoformat(),
        # "total_acquision_time_hour": get_total_hours(start_time, actual_end_time),
        "total_requests_made": total_request_made,
        "total_data_collected": total_collected_data,
    }
    print(acquisition_stats)
    create_stats_file(f"{data_dir}/{stats_filename}", acquisition_stats)


if __name__ == "__main__":
    main(duration_hours=2)
