import datetime as dt
import json
import os
import time
from typing import Any

from atproto import Client
from dotenv import load_dotenv

load_dotenv()
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")

SAFE_TIMESTAMP_FORMAT = r"%Y-%m-%dT%H-%M-%S-%f"


def utc_now():
    return dt.datetime.now(tz=dt.timezone.utc)


def get_total_hours(start_time: dt.datetime, end_time: dt.datetime) -> float:
    return round((end_time - start_time).total_seconds() / 3600, 2)


def make_list(obj: Any) -> list[Any]:
    return obj if isinstance(obj, list) else [] if obj is None else [obj]


def dump_json(filepath: str, obj: list[Any] | dict[str, Any]) -> None:
    with open(filepath, "w") as fout:
        json.dump(obj, fout, indent=4, ensure_ascii=False)


def load_json(filepath: str) -> list[Any] | dict[str, Any] | None:
    if os.path.exists(filepath):
        with open(filepath) as fin:
            return json.load(fin)


def update_data_file(filepath: str, obj: list[Any] | dict[str, Any]) -> None:
    dump_json(filepath, make_list(load_json(filepath)) + make_list(obj))


def main(queries: list[str], duration_hours: int = 24):
    client = Client()
    profile = client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)  # noqa
    request = client.app.bsky.feed.search_posts

    start_time = utc_now()
    end_time = start_time + dt.timedelta(hours=duration_hours // len(queries))

    data_dir = "./2025/data"
    base_filename = "br-bluesky-UGC-question-19"
    timestamp_label = start_time.strftime(SAFE_TIMESTAMP_FORMAT)
    data_filename = f"{base_filename}-data-{timestamp_label}.json"
    stats_filename = f"{base_filename}-stats-{timestamp_label}.json"

    total_requests_made = 0
    total_collected_data = 0
    for query in queries:
        cursor = "0"
        while utc_now() < end_time and total_collected_data < 10_500 and cursor:
            if total_requests_made > 0 and total_requests_made % 10 == 0:
                time.sleep(1)
            response = request({"q": query, "limit": 100, "cursor": cursor})
            cursor = response.cursor
            print(f"Cursor: {cursor}")
            data = [post.model_dump() for post in response.posts]
            total_requests_made += 1
            print(f"Requests: {total_requests_made}")
            total_collected_data += len(data)
            print(f"Posts: {total_collected_data}")
            update_data_file(f"{data_dir}/{data_filename}", data)

    actual_end_time = utc_now()
    total_hours = get_total_hours(start_time, actual_end_time)

    acquisition_stats = {
        "start_time": start_time.isoformat(),
        "end_time": actual_end_time.isoformat(),
        "queries": queries,
        "total_acquision_time_hour": total_hours,
        "total_requests_made": total_requests_made,
        "total_data_collected": total_collected_data,
    }
    dump_json(f"{data_dir}/{stats_filename}", acquisition_stats)


if __name__ == "__main__":
    main(["Climate", "Engineering"])
