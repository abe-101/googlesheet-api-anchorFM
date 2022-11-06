import json
import os
import pprint
import subprocess
import sys
import time

import feedparser
from dotenv import load_dotenv

from googleapi import get_values, update_values

load_dotenv()

YOUTUBE_TO_ANCHORFM = os.getenv("YOUTUBE_TO_ANCHORFM_DIR")
GOOGLESHEET_ID = os.getenv("GOOGLESHEET_ID")
ANCHORFM_RSS = os.getenv("ANCHORFM_RSS")


def youtube_url_to_id(url: str):
    if url[:-11] != "https://youtu.be/":
        sys.exit(f"invalid youtube url: {url}")
    return url[-11:]


def confirm_published(youtube_id):
    anchor = feedparser.parse(ANCHORFM_RSS)
    id_set = set()
    for entry in anchor["entries"]:
        id_set.add(entry["summary"][-15:-4])

    if youtube_id not in id_set:
        with open("failed.log", "a") as file:
            file.write(f"youtube id: {youtube_id} has yet to publish\n")
            print(f"youtube id: {youtube_id} has yet to publish\n")
        return False
    else:
        print(f"youtube id: {youtube_id} has been published!\n")
        return True


def publish_video(youtube_id: str):
    print(f"Attempting {youtube_id}")
    with open(YOUTUBE_TO_ANCHORFM + "episode.json", "w") as file:
        file.write(f'{{"id":"{youtube_id}"}}')

    os.chdir(YOUTUBE_TO_ANCHORFM)
    subprocess.run(["npm start"], shell=True)

    print(f"Finished {youtube_id}")


if __name__ == "__main__":
    check_for_complete = []
    g = get_values(GOOGLESHEET_ID, "A:F")
    for rowNum, row in enumerate(g["values"]):
        if rowNum != 0 and row[4] != "TRUE":
            youtube_id = youtube_url_to_id(row[1])
            print(f"Processing {youtube_id}")
            u = update_values(
                GOOGLESHEET_ID,
                "E" + str(rowNum + 1),
                "USER_ENTERED",
                [["TRUE"]],
            )
            publish_video(youtube_id)
            check_for_complete.append((youtube_id, str(rowNum + 1)))

    if len(check_for_complete) != 0:
        print("waiting for 5 min")
        time.sleep(300)
        for youtube_id, rowNum in check_for_complete:
            if confirm_published(youtube_id):
                u = update_values(
                    GOOGLESHEET_ID,
                    "F" + rowNum,
                    "USER_ENTERED",
                    [["TRUE"]],
                )
