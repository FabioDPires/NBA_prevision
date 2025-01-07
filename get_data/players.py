import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv3
import time
import utils

def remove_extra_columns(all_players_df):
    columns_to_remove = [
    'teamTricode', 'teamSlug', 'personId', 'firstName', 'familyName',
    'playerSlug', 'comment', 'jerseyNum',
    'fieldGoalsMade', 'fieldGoalsAttempted', 'fieldGoalsPercentage', 
    'threePointersMade', 'threePointersAttempted', 'threePointersPercentage',
    'freeThrowsMade', 'freeThrowsAttempted', 'freeThrowsPercentage',
    'reboundsOffensive', 'reboundsDefensive', 'reboundsTotal', 
    'assists', 'steals', 'blocks', 'turnovers', 'foulsPersonal', 
    'points', 'plusMinusPoints'
    ]

    all_players_df = all_players_df.drop(columns=columns_to_remove)
    return all_players_df


def get_all_game_ids(season,season_begin_date):
    game_ids = []
    
    game_finder = leaguegamefinder.LeagueGameFinder(
        league_id_nullable='00',
        season_nullable=season,
        date_from_nullable=season_begin_date,
    )
    games = game_finder.get_normalized_dict()['LeagueGameFinderResults']
    game_ids.extend([game['GAME_ID'] for game in games])

    game_ids = list(set(game_ids))

    return game_ids

def get_boxscore_traditional(game_id):
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()
    return player_stats

def get_players(season,season_begin_date):
    try:
        game_ids = get_all_game_ids(season,season_begin_date)
        df = pd.DataFrame(game_ids, columns=['GAME_ID'])

        if game_ids:
            print("Getting boxscores")
            all_player_boxscores = []
            
            for i, game_id in enumerate(game_ids):
                print(f"Getting boxscore for game {i+1}/{len(game_ids)}: {game_id}")
                player_stats = get_boxscore_traditional(game_id)
                all_player_boxscores.append(player_stats)
                time.sleep(1)
            
            print("Got boxscores successfully!")
            all_players_df = pd.concat(all_player_boxscores, ignore_index=True)
            all_players_df.loc[:, 'minutes'] = all_players_df['minutes'].apply(utils.extract_minutes)
            all_players_df.loc[all_players_df['minutes'] == 0, 'minutes'] = 1
            all_players_df = all_players_df[all_players_df['minutes'].notna()]
            all_players_df=remove_extra_columns(all_players_df)

            file_name = 'players.xlsx'
            all_players_df.to_excel(file_name, index=False)
        else:
            print("No games found")
    except Exception as e:
        print(f"Error getting boxscores: {e}")
