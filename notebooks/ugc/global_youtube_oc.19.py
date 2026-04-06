import os
import json
import datetime
import pickle

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

SAFE_TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S-%f"


def create_stats_file(filepath, stats_data):
    with open(filepath, "w") as fout:
        json.dump(stats_data, fout, indent=4)


def create_data_file(filepath, data):
    with open(filepath, "wb") as fout:
        pickle.dump(data, fout)


def get_total_hours(start_time, end_time):
    return round((end_time - start_time).total_seconds() / 3600, 2)


def main(duration_hours=24):

    api = build("youtube", "v3", developerKey=API_KEY)

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(hours=duration_hours)

    data_dir = "../../data"
    start_time_label = start_time.strftime(SAFE_TIMESTAMP_FORMAT)
    data_filename = f"br-youtube-UGC-question-19-data-{start_time_label}.pickle"
    stats_filename = f"br-youtube-UGC-question-19-stats-{start_time_label}.json"

    total_request_made = 0
    total_collected_data = 0

    queries = [# list of 20 queries that we will aim to get 10 pages of 50 results from each, for a total of 10,000 videos
        'cats', 'dogs', 'jazz', 'classic music', 'metal', 'kubernetes', 'docker', 'games', 'fps', 'rts',
        'politics', 'economy', 'social sciences', 'course', 'toy', 'horror', 'comedy', 'dance', 'astronomy', 'birds'
    ]
    
    daily_quota_exceeded = False
    query_idx = 0
    total_data = []
    next_page_token = None # None for the token will set the endpoint to give us the first page
    while (datetime.datetime.now() < end_time) and not daily_quota_exceeded:
        # DEVELOP UGC OC19 HERE
        try:
            response = api.search().list(
                part='snippet',# comma separated list of metadata that we want included in the response
                q=queries[query_idx],# query string to use in the search
                maxResults=50,# maximum value for this endpoint
                type='video',# search for videos
                pageToken=next_page_token# Token to control pagination of results
            ).execute()
            data = response['items']
            total_request_made += 1
            total_collected_data += len(data)
            total_data.append(data)
            # update_data_file(f"{data_dir}/{data_filename}", data)
            
            next_page_token = response.get('nextPageToken')

            print(f'request {total_request_made} completed. Collected a total of {total_collected_data} items.')
            if total_request_made % 10 == 0:
                query_idx += 1
                next_page_token = None# reset pagination token
                print(f'Got 10 pages for the query "{queries[query_idx-1]}"! now requesting videos for the next query "{queries[query_idx]}"')
            
        except HttpError as e:
            # Check if the error is specifically a Quota Exceeded error (HTTP 403)
            # and if the error message contains the 'quotaExceeded' reason.
            if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                print('daily quota exceeded!')
                daily_quota_exceeded = True
            else:
                print('another http error happened!')
                raise

    actual_end_time = datetime.datetime.now()

    acquisition_stats = {
        "start_time": start_time.isoformat(),
        "end_time": actual_end_time.isoformat(),
        "total_acquision_time_hour": get_total_hours(start_time, actual_end_time),
        "total_requests_made": total_request_made,
        "total_data_collected": total_collected_data,
        "daily_quota_exceeded": daily_quota_exceeded
    }
    create_stats_file(f"{data_dir}/{stats_filename}", acquisition_stats)
    create_data_file(f"{data_dir}/{data_filename}", total_data)


if __name__ == "__main__":
    main(duration_hours=24)
