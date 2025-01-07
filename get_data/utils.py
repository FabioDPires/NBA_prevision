import os
import re

def clean_data_folder():
    folder_path = "../model/data"
    files_to_delete = ["games.xlsx", "players.xlsx"]

    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

def extract_minutes(min_str):
    match = re.match(r'(\d+)', min_str)
    if match:
        return int(float(match.group(1)))
    return None