import os
import re

def update_data_folder():
    folder_path = "../model/data"
    files_to_delete = ["games.xlsx", "players.xlsx"]

    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

def clean_previous_data():
    folder = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(folder):
        if file.endswith(".xlsx"):
            filepath = os.path.join(folder, file)
            os.remove(filepath)


def extract_minutes(min_str):
    match = re.match(r'(\d+)', min_str)
    if match:
        return int(float(match.group(1)))
    return None