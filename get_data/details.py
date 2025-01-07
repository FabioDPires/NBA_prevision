import pandas as pd
from nba_api.stats.endpoints import scoreboardv2
import time

def get_all_line_scores(start_date,end_date):
    line_scores = []
    date_range = pd.date_range(start=start_date, end=end_date)

    for date in date_range:
        print(f"Getting line scores for {date.strftime('%Y-%m-%d')}...")
        attempts = 0
        while attempts < 3: 
            try:
                scoreboard = scoreboardv2.ScoreboardV2(
                    game_date=date.strftime('%Y-%m-%d'),
                    timeout=60
                )
                scores = scoreboard.get_normalized_dict()['LineScore']
                line_scores.extend(scores)
                print(f"Found {len(scores)} line scores.")
                break
            except Exception as e:
                attempts += 1
                print(f"Error on getting line scores for {date.strftime('%Y-%m-%d')}: {e}")
                time.sleep(2)
        
        time.sleep(1)

    return line_scores

def get_games_details(start_date,end_date):
    line_scores = get_all_line_scores(start_date,end_date)
    df_line_scores = pd.DataFrame(line_scores)
    df_line_scores.to_excel('line_scores.xlsx', index=False)
