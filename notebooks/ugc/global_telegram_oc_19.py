import os
import json
import datetime
import hashlib
import pickle

import asyncio

from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()
FILENAME = os.getenv("FILENAME")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

SAFE_TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S-%f"


def create_stats_file(filepath, stats_data):
    with open(filepath, "w") as fout:
        json.dump(stats_data, fout, indent=4)


def create_data_file(filepath, data):
    with open(filepath, "wb") as fout:
        pickle.dump(data, fout)


def get_total_hours(start_time, end_time):
    return round((end_time - start_time).total_seconds() / 3600, 2)


async def main(duration_hours=24, n_messages=10_100):# Attempting to gather over 10,000 messages in 24 hours

    api_client = TelegramClient(session=FILENAME, api_id=API_ID, api_hash=API_HASH)

    async with api_client:
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(hours=duration_hours)
    
        data_dir = "../../data"
        start_time_label = start_time.strftime(SAFE_TIMESTAMP_FORMAT)
        data_filename = f"br-telegram-UGC-question-19-data-{start_time_label}.pickle"
        stats_filename = f"br-telegram-UGC-question-19-stats-{start_time_label}.json"
    
        # total_request_made = 0
        total_collected_data = 0
        total_data = []
        completed_task = False
        # DEVELOP UGC OC19 HERE
        async for dialog in api_client.iter_dialogs():# Iterate through the dialogs our account participates
            hashed_dialog_id = hashlib.sha256(str(dialog.entity.id).encode('utf-8')).hexdigest()
            async for message in api_client.iter_messages(dialog.entity):# Iterate through the dialog's messages
                if not message.message:
                    continue
                hashed_message = hashlib.sha256(message.message.encode('utf-8')).hexdigest()
                data = {
                    'hashed_dialog_id': hashed_dialog_id,
                    'message_id': message.id,
                    'hashed_message': hashed_message,
                    'date': message.date.isoformat()
                }
                total_collected_data += 1
                total_data.append(data)
                if total_collected_data >= n_messages or datetime.datetime.now() >= end_time:# If number of collected messages is greater than n_messages or time ends, abort acquisition of data.
                    completed_task = True
                    break
            print(f'finished working with dialog {hashed_dialog_id}. Total messages until now: {total_collected_data}')
            if completed_task:
                break
    
        actual_end_time = datetime.datetime.now()

        acquisition_stats = {
            "start_time": start_time.isoformat(),
            "end_time": actual_end_time.isoformat(),
            "total_acquision_time_hour": get_total_hours(start_time, actual_end_time),
            "total_data_collected": total_collected_data,
        }
        create_stats_file(f"{data_dir}/{stats_filename}", acquisition_stats)
        create_data_file(f"{data_dir}/{data_filename}", total_data)


if __name__ == "__main__":
    asyncio.run(main(duration_hours=24, n_messages=10_100))
