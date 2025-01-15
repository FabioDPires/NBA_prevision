import os
import re
from datetime import datetime, timedelta
import shutil
import git

def update_data_folder():
    
    folder_path = "../model/data"
    files_to_delete = ["games.xlsx", "players.xlsx"]

    for file_name in files_to_delete:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    games_file = os.path.join(os.getcwd(), 'games.xlsx')
    players_file = os.path.join(os.getcwd(), 'players.xlsx')
    shutil.move(games_file, os.path.join(folder_path, 'games.xlsx'))
    shutil.move(players_file, os.path.join(folder_path, 'players.xlsx'))

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

def getPreviousDay():
    current_date = datetime.now()
    previous_day = current_date - timedelta(days=1)
    formatted_date = previous_day.strftime('%Y-%m-%d')
    return formatted_date

def commit_changes():
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
        while not os.path.isdir(os.path.join(current_path, '.git')):
            current_path = os.path.dirname(current_path)
            if current_path == os.path.dirname(current_path):
                raise git.exc.InvalidGitRepositoryError("Não foi possível encontrar o repositório Git.")

        repo = git.Repo(current_path)

        files_to_commit = [
            'model/data/games.xlsx',
            'model/data/players.xlsx'
        ]

        changed_files = [file for file in files_to_commit if os.path.exists(os.path.join(current_path, file)) and repo.is_dirty(path=file)]

        if changed_files:
            repo.git.add(changed_files)
            repo.index.commit("Updated data")
            origin = repo.remote(name='origin')
            origin.push()
        else:
            print("No changes made.")

    except git.exc.InvalidGitRepositoryError:
        print("Error: Repository not found")
    except Exception as e:
        print(f"Error: {e}")