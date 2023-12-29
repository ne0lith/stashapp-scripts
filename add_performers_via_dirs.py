import os
import json
import requests
from pathlib import Path

# This script will add new performers to your stashapp via your directory structure.
# This script assumes your performer directory structure is as follows:
#
# PERFORMERS_ROOT
# ├── performer_name
# │   └── (files and subdirectories under performer_name)
# ├── performer_name2
# │   └── (files and subdirectories under performer_name2)
# ├── performer_name3
# │   └── (files and subdirectories under performer_name3)
# └── etc
#     └── (files and subdirectories under etc)
#
# GRAPHQL_URL is your stashapp graphql endpoint
# BLACKLIST_PERFORMERS is a list of performers to skip
# SKIP_CHOICE will skip inputting y/n to add each performer
# AUTOTAG_SCENES will send the payload to autotag scenes for each performer

PERFORMERS_ROOT = "path/to/your/performers"
GRAPHQL_URL = "http://localhost:9999/graphql"
BLACKLIST_PERFORMERS = ["misc", "studios"]
SKIP_CHOICE = False
AUTOTAG_SCENES = True


def get_direct_subfolders(root_path):
    root_dir = Path(root_path)

    if not root_dir.is_dir():
        raise ValueError(f"The provided path '{root_dir}' is not a valid directory.")

    subfolders = [
        subfolder.name for subfolder in root_dir.iterdir() if subfolder.is_dir()
    ]

    return subfolders


def payload_find_performer(query_param):
    return {
        "operationName": "FindPerformers",
        "variables": {
            "filter": {
                "q": query_param,
                "page": 1,
                "per_page": 40,
                "sort": "name",
                "direction": "ASC",
            },
            "performer_filter": {},
        },
        "query": "query FindPerformers($filter: FindFilterType, $performer_filter: PerformerFilterType, $performer_ids: [Int!]) {\n  findPerformers(\n    filter: $filter\n    performer_filter: $performer_filter\n    performer_ids: $performer_ids\n  ) {\n    count\n    performers {\n      ...PerformerData\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PerformerData on Performer {\n  id\n  name\n  disambiguation\n  url\n  gender\n  twitter\n  instagram\n  birthdate\n  ethnicity\n  country\n  eye_color\n  height_cm\n  measurements\n  fake_tits\n  penis_length\n  circumcised\n  career_length\n  tattoos\n  piercings\n  alias_list\n  favorite\n  ignore_auto_tag\n  image_path\n  scene_count\n  image_count\n  gallery_count\n  movie_count\n  performer_count\n  o_counter\n  tags {\n    ...SlimTagData\n    __typename\n  }\n  stash_ids {\n    stash_id\n    endpoint\n    __typename\n  }\n  rating100\n  details\n  death_date\n  hair_color\n  weight\n  __typename\n}\n\nfragment SlimTagData on Tag {\n  id\n  name\n  aliases\n  image_path\n  parent_count\n  child_count\n  __typename\n}",
    }


def payload_create_performer(query_param):
    return {
        "operationName": "PerformerCreate",
        "variables": {
            "input": {
                "name": query_param,
                "disambiguation": "",
                "alias_list": [],
                "gender": None,
                "birthdate": "",
                "death_date": "",
                "country": "",
                "ethnicity": "",
                "hair_color": "",
                "eye_color": "",
                "height_cm": None,
                "weight": None,
                "measurements": "",
                "fake_tits": "",
                "penis_length": None,
                "circumcised": None,
                "tattoos": "",
                "piercings": "",
                "career_length": "",
                "url": "",
                "twitter": "",
                "instagram": "",
                "details": "",
                "tag_ids": [],
                "ignore_auto_tag": False,
                "stash_ids": [],
            }
        },
        "query": "mutation PerformerCreate($input: PerformerCreateInput!) {\n  performerCreate(input: $input) {\n    ...PerformerData\n    __typename\n  }\n}\n\nfragment PerformerData on Performer {\n  id\n  name\n  disambiguation\n  url\n  gender\n  twitter\n  instagram\n  birthdate\n  ethnicity\n  country\n  eye_color\n  height_cm\n  measurements\n  fake_tits\n  penis_length\n  circumcised\n  career_length\n  tattoos\n  piercings\n  alias_list\n  favorite\n  ignore_auto_tag\n  image_path\n  scene_count\n  image_count\n  gallery_count\n  movie_count\n  performer_count\n  o_counter\n  tags {\n    ...SlimTagData\n    __typename\n  }\n  stash_ids {\n    stash_id\n    endpoint\n    __typename\n  }\n  rating100\n  details\n  death_date\n  hair_color\n  weight\n  __typename\n}\n\nfragment SlimTagData on Tag {\n  id\n  name\n  aliases\n  image_path\n  parent_count\n  child_count\n  __typename\n}",
    }


def payload_performer_autotag(performer_id):
    return {
        "operationName": "MetadataAutoTag",
        "variables": {"input": {"performers": [performer_id]}},
        "query": "mutation MetadataAutoTag($input: AutoTagMetadataInput!) {\n  metadataAutoTag(input: $input)\n}",
    }


def send_graphql_request(payload):
    HEADERS = {"Content-Type": "application/json"}
    response = requests.post(GRAPHQL_URL, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        return None


def performer_exists(query_param):
    payload = payload_find_performer(query_param)
    response = send_graphql_request(payload)

    if response and "data" in response and "findPerformers" in response["data"]:
        count = response["data"]["findPerformers"]["count"]
        if count > 0:
            performers = response["data"]["findPerformers"]["performers"]
            performer_id = performers[0]["id"]
            return performer_id

    return False


def add_performer(performer_name, autotag_scenes=False):
    query_param = performer_name

    if performer_exists(query_param):
        print(f"Performer: {query_param}")
        print("Error: Already exists.")
    else:
        create_payload = payload_create_performer(query_param)
        result = send_graphql_request(create_payload)

        if result and "data" in result and "performerCreate" in result["data"]:
            performer_id = result["data"]["performerCreate"]["id"]
            print(f"Created Performer: {query_param}")
            print(f"Created with ID: {performer_id}")

    if autotag_scenes:
        performer_id = (
            performer_exists(query_param)
            if performer_exists(query_param)
            else performer_id
        )
        autotag_payload = payload_performer_autotag(performer_id)
        autotag_result = send_graphql_request(autotag_payload)
        print(f"Autotagging: {'started' if autotag_result else 'failed'}")


def main():
    os.system("cls" if os.name == "nt" else "clear")

    blacklist = BLACKLIST_PERFORMERS
    performers = get_direct_subfolders(PERFORMERS_ROOT)

    for performer in performers:
        if any(x in performer.lower() for x in blacklist):
            print(f"Skipping: {performer}")
            continue

        if not SKIP_CHOICE:
            choice = input(f"Add performer: {performer}? (y/n): ")
            if choice.lower() != "y":
                print(f"Skipping: {performer}\n")
                continue

        add_performer(performer, autotag_scenes=AUTOTAG_SCENES)
        print()


if __name__ == "__main__":
    main()
