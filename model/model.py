import streamlit as st
import requests
from collections import defaultdict
from datetime import date
from datetime import datetime
import json
import pandas as pd
import os
from env import LOCAL_DATA_DIRECTORY, STREAMLIT_DATA_DIRECTORY,LOCAL_MODEL_DIRECTORY,STREAMLIT_MODEL_DIRECTORY,LOCAL_LOGOS_DIRECTORY,STREAMLIT_LOGOS_DIRECTORY
import joblib
import numpy as np
import io 
from PIL import Image
import base64
from io import BytesIO

def get_nba_season_id(date):
    if date.month in range(1, 7):
        return date.year - 1
    else:
        return date.year


def get_schedule(date,season_id):
    # Define a URL
    url = f"https://stats.nba.com/stats/internationalbroadcasterschedule?LeagueID=00&Season={season_id}&RegionID=0&Date={date}&EST=Y"

    # Define os cabeçalhos
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://stats.nba.com/",
        "Origin": "https://stats.nba.com",
        "Accept": "application/json, text/plain, */*"
    }

    # Faz a solicitação GET
    response = requests.get(url, headers=headers)

    # Verifica se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Carrega os dados JSON da resposta
        data = response.json()
        
        # Verifica se o 'CompleteGameList' está presente nos 'resultSets'
        complete_game_list = []
        for resultSet in data.get('resultSets', []):
            if 'CompleteGameList' in resultSet:
                complete_game_list = resultSet['CompleteGameList']
                break
        
        # Armazena os jogos em um array e remove duplicatas
        games_array = []
        seen_game_ids = set()
        
        for game in complete_game_list:
            game_id = game["gameID"]
            if game_id not in seen_game_ids:
                game_info = {
                    "GAME_ID": game_id,
                    "VISITOR_TEAM_NAME" :  game["vtNickName"],
                    "HOME_TEAM_NAME" :  game["htNickName"],
                    "GAME_DATE": game["date"],
                }
                games_array.append(game_info)
                seen_game_ids.add(game_id)
        
        return games_array
    else:
        print(f"Falha ao acessar os dados. Status code: {response.status_code}")
        return None

def add_team_info(game, teams):
    home_team_info = teams.loc[teams['nickname'] == game['HOME_TEAM_NAME'], ['id', 'year_founded']]
    if not home_team_info.empty:
        home_team_id = home_team_info['id'].values[0]
        home_team_foundation = home_team_info['year_founded'].values[0]
    else:
        home_team_id = None
        home_team_foundation = None
    if home_team_foundation is None:
        raise ValueError("Value error")

    visitor_team_info = teams.loc[teams['nickname'] == game['VISITOR_TEAM_NAME'], ['id', 'year_founded']]
    if not visitor_team_info.empty:
        visitor_team_id = visitor_team_info['id'].values[0]
        visitor_team_foundation = visitor_team_info['year_founded'].values[0]
    else:
        visitor_team_id = None
        visitor_team_foundation = None

    if visitor_team_foundation is None:
        raise ValueError("Value error")

    game['HOME_TEAM_ID'] = home_team_id
    game['FOUNDATION_HOME'] = int(home_team_foundation)
    game['VISITOR_TEAM_ID'] = visitor_team_id
    game['FOUNDATION_VISITOR'] = int(visitor_team_foundation)
    
    return game

def calculate_team_stats(team_id, pd_games, season_id, selected_date):
    team_games = pd_games[
        (pd_games['SEASON'] == season_id) & 
        (pd_games['GAME_DATE_EST'] < selected_date) & 
        ((pd_games['HOME_TEAM_ID'] == team_id) | (pd_games['VISITOR_TEAM_ID'] == team_id))
    ]

    total_games = len(team_games)
    total_wins = (
        ((team_games['HOME_TEAM_ID'] == team_id) & (team_games['HOME_TEAM_WINS'] == 1)) |
        ((team_games['VISITOR_TEAM_ID'] == team_id) & (team_games['HOME_TEAM_WINS'] == 0))
    ).sum()
    total_losses = total_games - total_wins
    win_percentage = round(total_wins / total_games if total_games > 0 else 0.0, 3)

    return total_games, int(total_wins), int(total_losses), win_percentage


def calculate_team_stats_at_home(team_id,pd_games,season_id,selected_date):     
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & (pd_games['HOME_TEAM_ID'] == team_id)]
    total_games_at_home = len(team_games)

    wins_at_home = 0
    for i, g in team_games.iterrows():
        if g['HOME_TEAM_WINS'] == 1:
            wins_at_home += 1
    
    losses_at_home = total_games_at_home - wins_at_home
    win_percentage_at_home = round(wins_at_home / total_games_at_home if total_games_at_home > 0 else 0.0, 3)
    
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=False)

    win_streak = 0
    for i, g in team_games.iterrows():
        if team_id == g['HOME_TEAM_ID'] and g['HOME_TEAM_WINS'] == 1:
            win_streak += 1
        else:
            break

    losses_streak = 0
    for i, g in team_games.iterrows():
        if team_id == g['HOME_TEAM_ID'] and g['HOME_TEAM_WINS'] == 0:
            losses_streak += 1
        else:
            break
   
    if win_streak > 0 :
        streak = win_streak
    else:
        streak=losses_streak * -1

    return losses_at_home,win_percentage_at_home,streak

def calculate_team_stats_away(team_id,pd_games,season_id,selected_date):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & (pd_games['VISITOR_TEAM_ID'] == team_id)]
    away_games = len(team_games)

    away_wins = 0
    for index, game in team_games.iterrows():
        if game['HOME_TEAM_WINS'] == 0:
            away_wins += 1

    win_percentage_away = round(away_wins / away_games if away_games > 0 else 0.0, 3)
    return win_percentage_away

def calculate_team_stats_last_games(team_id,pd_games,season_id,selected_date,num_games):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & 
                    ((pd_games['HOME_TEAM_ID'] == team_id) | (pd_games['VISITOR_TEAM_ID'] == team_id))]
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=True)

    num_available_games = len(team_games)
    
    if num_available_games == 0:
        avg_points = 0
        avg_conceded = 0
        avg_assists = 0
        avg_fgpct=0
        avg_ftpct = 0
        avg_fg3pct = 0
        avg_reb = 0

    else:
        relevant_games = team_games.tail(min(num_games, num_available_games))
        total_points = 0
        total_conceded = 0
        total_assists = 0
        total_fgpct=0
        total_ftpct = 0
        total_fg3pct = 0
        total_reb = 0
        for i, g in relevant_games.iterrows():
            if team_id == g['HOME_TEAM_ID']:
                total_points += g['PTS_home']
                total_conceded +=g['PTS_away']
                total_assists += g['AST_home']
                total_fgpct += g['FG_PCT_home']
                total_ftpct += g['FT_PCT_home']
                total_fg3pct += g['FG3_PCT_home']
                total_reb += g['REB_home']
            else:
                total_points += g['PTS_away']
                total_conceded += g['PTS_home']
                total_assists += g['AST_away']
                total_fgpct += g['FG_PCT_away']
                total_ftpct += g['FT_PCT_away']
                total_fg3pct += g['FG3_PCT_away']
                total_reb += g['REB_away']  
    
        avg_points = total_points / len(relevant_games)
        avg_conceded = total_conceded / len(relevant_games)
        avg_assists = total_assists / len(relevant_games)
        avg_fgpct = total_fgpct / len(relevant_games)
        avg_ftpct = total_ftpct / len(relevant_games)
        avg_fg3pct = total_fg3pct / len(relevant_games)
        avg_reb = total_reb / len(relevant_games)
        
        avg_points = round(avg_points, 2)
        avg_conceded = round(avg_conceded, 2)
        avg_assists = round(avg_assists, 2)
        avg_fgpct = round(avg_fgpct, 2)
        avg_ftpct = round(avg_ftpct, 2)
        avg_fg3pct = round(avg_fg3pct, 2)
        avg_reb = round(avg_reb, 2)
 
    return avg_points,avg_conceded,avg_assists,avg_fgpct,avg_ftpct,avg_fg3pct,avg_reb

def calculate_team_stats_last_games_at_home(team_id,pd_games,season_id,selected_date,num_games):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & 
                    (pd_games['HOME_TEAM_ID'] == team_id)]
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=True)
    
    num_available_games = len(team_games)

    if num_available_games == 0:
        avg_points=0
        avg_conceded =0
        avg_assists=0
        avg_reb=0

    else:
        relevant_games = team_games.tail(min(num_games, num_available_games))
        total_points = relevant_games['PTS_home'].sum()
        total_conceded = relevant_games['PTS_away'].sum()
        total_assists = relevant_games['AST_home'].sum()
        total_reb = relevant_games['REB_home'].sum()
       
        avg_points= total_points / len(relevant_games)
        avg_conceded= total_conceded / len(relevant_games)
        avg_assists= total_assists / len(relevant_games)
        avg_reb= total_reb / len(relevant_games)

        avg_points = round(avg_points, 2)
        avg_conceded = round(avg_conceded, 2)
        avg_assists = round(avg_assists, 2)
        avg_reb = round(avg_reb, 2)

    return avg_points,avg_conceded,avg_assists,avg_reb
 
def calculate_team_stats_last_games_away(team_id,pd_games,season_id,selected_date,num_games):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & 
                    (pd_games['VISITOR_TEAM_ID'] == team_id)]
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=True)                
    
    num_available_games = len(team_games)
    
    if num_available_games == 0:
        avg_points = 0
        avg_conceded = 0
        avg_assists = 0
        avg_fg3pct = 0
        avg_reb = 0

    else:
        relevant_games = team_games.tail(min(num_games, num_available_games))
        total_points = relevant_games['PTS_away'].sum()
        total_conceded = relevant_games['PTS_home'].sum()
        total_assists = relevant_games['AST_away'].sum()
        total_fg3pct = relevant_games['FG3_PCT_away'].sum()
        total_reb = relevant_games['REB_away'].sum()

        avg_points=total_points / len(relevant_games)
        avg_conceded=total_conceded / len(relevant_games)
        avg_assists=total_assists / len(relevant_games)
        avg_fg3pct=total_fg3pct / len(relevant_games)
        avg_reb=total_reb / len(relevant_games)

        avg_points = round(avg_points, 2)
        avg_conceded = round(avg_conceded, 2)
        avg_assists = round(avg_assists, 2)
        avg_fg3pct = round(avg_fg3pct, 2)
        avg_reb = round(avg_reb, 2)

    return avg_points,avg_conceded,avg_assists,avg_fg3pct,avg_reb

def calculate_players_usage(team_id,pd_games,pd_players,season_id,selected_date,num_games):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & 
                    ((pd_games['HOME_TEAM_ID'] == team_id) | (pd_games['VISITOR_TEAM_ID'] == team_id))]
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=True)  

    num_available_games = len(team_games)
    
    if num_available_games == 0:
        avg_minutes = 0.0     
    else:
        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'HOME_TEAM_ID'], right_on=['gameId', 'teamId'])
        home_team_total_minutes = tmp.groupby(['GAME_ID', 'HOME_TEAM_ID'])['minutes'].sum().reset_index(name='HOME_TEAM_TOTAL_MINUTES')
        team_games = pd.merge(team_games, home_team_total_minutes, on=['GAME_ID', 'HOME_TEAM_ID'], how='left')
        
        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'VISITOR_TEAM_ID'], right_on=['gameId', 'teamId'])
        away_team_total_minutes = tmp.groupby(['GAME_ID', 'VISITOR_TEAM_ID'])['minutes'].sum().reset_index(name='VISITOR_TEAM_TOTAL_MINUTES')
        team_games = pd.merge(team_games, away_team_total_minutes, on=['GAME_ID', 'VISITOR_TEAM_ID'], how='left')

        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'HOME_TEAM_ID'], right_on=['gameId', 'teamId'])
        home_team_count = tmp.groupby(['GAME_ID', 'HOME_TEAM_ID']).size().reset_index(name='HOME_TEAM_USED_PLAYERS')
        team_games = pd.merge(team_games, home_team_count, on=['GAME_ID', 'HOME_TEAM_ID'], how='left')

        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'VISITOR_TEAM_ID'], right_on=['gameId', 'teamId'])
        away_team_count = tmp.groupby(['GAME_ID', 'VISITOR_TEAM_ID']).size().reset_index(name='VISITOR_TEAM_USED_PLAYERS')
        team_games = pd.merge(team_games, away_team_count, on=['GAME_ID', 'VISITOR_TEAM_ID'], how='left')
        
        team_games['HOME_TEAM_TOTAL_MINUTES'] = pd.to_numeric(team_games['HOME_TEAM_TOTAL_MINUTES'], errors='coerce')
        team_games['VISITOR_TEAM_TOTAL_MINUTES'] = pd.to_numeric(team_games['VISITOR_TEAM_TOTAL_MINUTES'], errors='coerce')

        team_games['HOME_TEAM_AVG_MINUTES'] = team_games['HOME_TEAM_TOTAL_MINUTES'] / team_games['HOME_TEAM_USED_PLAYERS']
        team_games['HOME_TEAM_AVG_MINUTES'] = team_games['HOME_TEAM_AVG_MINUTES'].round(2)

        team_games['VISITOR_TEAM_AVG_MINUTES'] = team_games['VISITOR_TEAM_TOTAL_MINUTES'] / team_games['VISITOR_TEAM_USED_PLAYERS']
        team_games['VISITOR_TEAM_AVG_MINUTES'] = team_games['VISITOR_TEAM_AVG_MINUTES'].round(2)

        relevant_games = team_games.tail(min(num_games, num_available_games))
        
        total = 0

        for index, g in relevant_games.iterrows():

            if team_id == g['HOME_TEAM_ID']:
                total += g['HOME_TEAM_AVG_MINUTES']
            else:
                total += g['VISITOR_TEAM_AVG_MINUTES']
    
        avg_minutes = total/len(relevant_games)
        avg_minutes = round(avg_minutes, 2)

    return avg_minutes

def calculate_starters_usage(team_id,pd_games,pd_players,season_id,selected_date,num_games):
    team_games = pd_games[(pd_games['SEASON'] == season_id) & (pd_games['GAME_DATE_EST'] < selected_date) & 
                    ((pd_games['HOME_TEAM_ID'] == team_id) | (pd_games['VISITOR_TEAM_ID'] == team_id))]
    team_games = team_games.sort_values(by='GAME_DATE_EST', ascending=True)  

    num_available_games = len(team_games)
    
    if num_available_games == 0:
        avg_minutes = 0.0
    else:
        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'HOME_TEAM_ID'], right_on=['gameId', 'teamId'])
        filtered_tmp = tmp[tmp['position'].isin(['F', 'C', 'G'])]
        home_team_starters_total_minutes = filtered_tmp.groupby(['GAME_ID', 'HOME_TEAM_ID'])['minutes'].sum().reset_index(name='HOME_TEAM_STARTERS_TOTAL_MINUTES')
        team_games = pd.merge(team_games, home_team_starters_total_minutes, on=['GAME_ID', 'HOME_TEAM_ID'], how='left')

        tmp = pd.merge(team_games, pd_players, left_on=['GAME_ID', 'VISITOR_TEAM_ID'], right_on=['gameId', 'teamId'])
        filtered_tmp = tmp[tmp['position'].isin(['F', 'C', 'G'])]
        away_team_starters_total_minutes = filtered_tmp.groupby(['GAME_ID', 'VISITOR_TEAM_ID'])['minutes'].sum().reset_index(name='VISITOR_TEAM_STARTERS_TOTAL_MINUTES')
        team_games = pd.merge(team_games, away_team_starters_total_minutes, on=['GAME_ID', 'VISITOR_TEAM_ID'], how='left')
        
        team_games['HOME_TEAM_STARTERS_TOTAL_MINUTES'] = pd.to_numeric(team_games['HOME_TEAM_STARTERS_TOTAL_MINUTES'], errors='coerce')
        team_games['VISITOR_TEAM_STARTERS_TOTAL_MINUTES'] = pd.to_numeric(team_games['VISITOR_TEAM_STARTERS_TOTAL_MINUTES'], errors='coerce')

        team_games['HOME_TEAM_STARTERS_AVG_MINUTES'] = team_games['HOME_TEAM_STARTERS_TOTAL_MINUTES'] / 5
        team_games['HOME_TEAM_STARTERS_AVG_MINUTES'] = team_games['HOME_TEAM_STARTERS_AVG_MINUTES'].round(2)

        team_games['VISITOR_TEAM_STARTERS_AVG_MINUTES'] = team_games['VISITOR_TEAM_STARTERS_TOTAL_MINUTES'] / 5
        team_games['VISITOR_TEAM_STARTERS_AVG_MINUTES'] = team_games['VISITOR_TEAM_STARTERS_AVG_MINUTES'].round(2)

        relevant_games = team_games.tail(min(num_games, num_available_games))
        total = 0
        for index, g in relevant_games.iterrows():
            if team_id == g['HOME_TEAM_ID']:
                total += g['HOME_TEAM_STARTERS_AVG_MINUTES']
            else:
                total += g['VISITOR_TEAM_STARTERS_AVG_MINUTES']
            
        avg_minutes = total/len(relevant_games)
        avg_minutes = round(avg_minutes, 2)

    return avg_minutes

def add_game_info(game, pd_games,pd_players, season_id, selected_date):
    selected_date = pd.to_datetime(selected_date)
    pd_games['GAME_DATE_EST'] = pd.to_datetime(pd_games['GAME_DATE_EST'])
    pd_games_sorted = pd_games.sort_values(by='GAME_DATE_EST')

    #HOME TEAM
    home_team_id = game["HOME_TEAM_ID"]
    home_stats = calculate_team_stats(home_team_id, pd_games, season_id, selected_date)
    game['HOME_TEAM_TOTAL_GAMES'], game['HOME_TEAM_TOTAL_WINS'], game['HOME_TEAM_TOTAL_LOSSES'], game['HOME_TEAM_WIN_PERCENTAGE'] = home_stats

    home_stats_at_home=calculate_team_stats_at_home(home_team_id,pd_games,season_id,selected_date)
    game['HOME_TEAM_TOTAL_LOSSES_AT_HOME'], game['HOME_TEAM_WIN_PERCENTAGE_AT_HOME'],game['HOME_TEAM_WIN/LOSS_STREAK_AT_HOME'] = home_stats_at_home

    home_stats_last_n_games=calculate_team_stats_last_games(home_team_id,pd_games,season_id,selected_date,5)
    game['AVG_POINTS_LAST_5_GAMES_HOME_TEAM'],game['AVG_POINTS_CONCEDED_LAST_5_GAMES_HOME_TEAM'],game['AVG_ASSISTS_LAST_5_GAMES_HOME_TEAM'],game['AVG_FGPCT_LAST_5_GAMES_HOME_TEAM'],game['AVG_FTPCT_LAST_5_GAMES_HOME_TEAM'],game['AVG_FG3PCT_LAST_5_GAMES_HOME_TEAM'],game['AVG_REB_LAST_5_GAMES_HOME_TEAM'] = home_stats_last_n_games

    home_stats_last_n_games_at_home=calculate_team_stats_last_games_at_home(home_team_id,pd_games,season_id,selected_date,5)
    game['AVG_POINTS_LAST_5_GAMES_AT_HOME_HOME_TEAM'],game['AVG_POINTS_CONCEDED_LAST_5_GAMES_AT_HOME_HOME_TEAM'],game['AVG_ASSISTS_LAST_5_GAMES_AT_HOME_HOME_TEAM'],game['AVG_REB_LAST_5_GAMES_AT_HOME_HOME_TEAM'] = home_stats_last_n_games_at_home
    
    home_players_used=calculate_players_usage(home_team_id,pd_games,pd_players,season_id,selected_date,4)
    game['AVG_MINUTES_LAST_4_GAMES_HOME_TEAM'] = home_players_used

    home_starters_used=calculate_starters_usage(home_team_id,pd_games,pd_players,season_id,selected_date,4)
    game['AVG_MINUTES_STARTERS_LAST_4_GAMES_HOME_TEAM'] = home_starters_used
    
    
    
    #AWAY TEAM
    visitor_team_id = game["VISITOR_TEAM_ID"]
    visitor_stats = calculate_team_stats(visitor_team_id, pd_games, season_id, selected_date)
    game['AWAY_TEAM_TOTAL_GAMES'], game['AWAY_TEAM_TOTAL_WINS'], game['AWAY_TEAM_TOTAL_LOSSES'], game['AWAY_TEAM_WIN_PERCENTAGE'] = visitor_stats

    visitor_stats_away = calculate_team_stats_away(visitor_team_id,pd_games,season_id,selected_date)
    game['AWAY_TEAM_WIN_PERCENTAGE_AWAY'] = visitor_stats_away

    away_stats_last_n_games=calculate_team_stats_last_games(visitor_team_id,pd_games,season_id,selected_date,5)
    game['AVG_POINTS_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_POINTS_CONCEDED_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_ASSISTS_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_FGPCT_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_FTPCT_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_FG3PCT_LAST_5_GAMES_VISITOR_TEAM'],game['AVG_REB_LAST_5_GAMES_VISITOR_TEAM'] = away_stats_last_n_games
    
    away_stats_last_n_games_away=calculate_team_stats_last_games_away(visitor_team_id,pd_games,season_id,selected_date,5)
    game['AVG_POINTS_LAST_5_GAMES_AWAY_VISITOR_TEAM'],game['AVG_POINTS_CONCEDED_LAST_5_GAMES_AWAY_VISITOR_TEAM'],game['AVG_ASSISTS_LAST_5_GAMES_AWAY_VISITOR_TEAM'],game['AVG_FG3PCT_LAST_5_GAMES_AWAY_VISITOR_TEAM'],game['AVG_REB_LAST_5_GAMES_AWAY_VISITOR_TEAM'] = away_stats_last_n_games_away
    
    away_players_used=calculate_players_usage(visitor_team_id,pd_games,pd_players,season_id,selected_date,4)
    game['AVG_MINUTES_LAST_4_GAMES_VISITOR_TEAM'] = away_players_used

    away_starters_used=calculate_starters_usage(visitor_team_id,pd_games,pd_players,season_id,selected_date,4)
    game['AVG_MINUTES_STARTERS_LAST_4_GAMES_VISITOR_TEAM'] = away_starters_used

    return game

def process_input(input_data):
    processed_data = [
        input_data["HOME_TEAM_TOTAL_GAMES"],
        input_data["HOME_TEAM_TOTAL_WINS"],
        input_data["AWAY_TEAM_TOTAL_WINS"],
        input_data["HOME_TEAM_TOTAL_LOSSES"],
        input_data["AWAY_TEAM_TOTAL_LOSSES"],
        input_data["HOME_TEAM_WIN_PERCENTAGE"],
        input_data["AWAY_TEAM_WIN_PERCENTAGE"],
        input_data["HOME_TEAM_TOTAL_LOSSES_AT_HOME"],
        input_data["HOME_TEAM_WIN_PERCENTAGE_AT_HOME"],
        input_data["AWAY_TEAM_WIN_PERCENTAGE_AWAY"],
        input_data["HOME_TEAM_WIN/LOSS_STREAK_AT_HOME"],
        input_data["AVG_POINTS_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_POINTS_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_POINTS_CONCEDED_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_POINTS_CONCEDED_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_ASSISTS_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_ASSISTS_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_FGPCT_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_FGPCT_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_FTPCT_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_FTPCT_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_FG3PCT_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_FG3PCT_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_REB_LAST_5_GAMES_HOME_TEAM"],
        input_data["AVG_REB_LAST_5_GAMES_VISITOR_TEAM"],
        input_data["AVG_POINTS_LAST_5_GAMES_AT_HOME_HOME_TEAM"],
        input_data["AVG_POINTS_CONCEDED_LAST_5_GAMES_AT_HOME_HOME_TEAM"],
        input_data["AVG_ASSISTS_LAST_5_GAMES_AT_HOME_HOME_TEAM"],
        input_data["AVG_REB_LAST_5_GAMES_AT_HOME_HOME_TEAM"],
        input_data["AVG_POINTS_LAST_5_GAMES_AWAY_VISITOR_TEAM"],
        input_data["AVG_POINTS_CONCEDED_LAST_5_GAMES_AWAY_VISITOR_TEAM"],
        input_data["AVG_ASSISTS_LAST_5_GAMES_AWAY_VISITOR_TEAM"],
        input_data["AVG_FG3PCT_LAST_5_GAMES_AWAY_VISITOR_TEAM"],
        input_data["AVG_REB_LAST_5_GAMES_AWAY_VISITOR_TEAM"],
        input_data["FOUNDATION_HOME"],
        input_data["FOUNDATION_VISITOR"],
        input_data["AVG_MINUTES_LAST_4_GAMES_HOME_TEAM"],
        input_data["AVG_MINUTES_LAST_4_GAMES_VISITOR_TEAM"],
        input_data["AVG_MINUTES_STARTERS_LAST_4_GAMES_HOME_TEAM"],
        input_data["AVG_MINUTES_STARTERS_LAST_4_GAMES_VISITOR_TEAM"]
    ]
    return np.array(processed_data).reshape(1, -1)

def predict(input_data):
    return model.predict(input_data)

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def display_team_matchup(visitor_team_name, home_team_name, visitor_logo_url, home_logo_url, prediction):
    visitor_logo = Image.open(visitor_logo_url)
    home_logo = Image.open(home_logo_url)

    visitor_logo_base64 = image_to_base64(visitor_logo)
    home_logo_base64 = image_to_base64(home_logo)
    
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <div style='text-align: center; margin-right: 30px;'>
                <img src='data:image/png;base64,{visitor_logo_base64}' width='100' height='100' style='display: block; margin: auto;' />
                <div><strong>{visitor_team_name}</strong></div>
            </div>
            <div style='text-align: center; margin: 0 30px; font-size: 32px;'>
                @
            </div>
            <div style='text-align: center; margin-left: 30px;'>
                <img src='data:image/png;base64,{home_logo_base64}' width='100' height='100' style='display: block; margin: auto;' />
                <div><strong>{home_team_name}</strong></div>
            </div>
        </div>
        <div style='text-align: center; margin-top: 20px;'>
            <strong>Prediction: {prediction} Wins</strong>
        </div>
        <hr style='margin-top: 20px;' />
    """, unsafe_allow_html=True)



nba_teams_file_path = os.path.join(STREAMLIT_DATA_DIRECTORY, 'nba_teams.xlsx')
games_file_path = os.path.join(STREAMLIT_DATA_DIRECTORY, 'games.xlsx')
players_file_path = os.path.join(STREAMLIT_DATA_DIRECTORY, 'players.xlsx')
pd_teams = pd.read_excel(nba_teams_file_path)
pd_games = pd.read_excel(games_file_path)
pd_players = pd.read_excel(players_file_path)

model_path = os.path.join(STREAMLIT_MODEL_DIRECTORY, 'prevision_model.pkl')
model = joblib.load(model_path)


title_html = """
    <style>
    .title {
        text-align: center;
    }
    </style>
    <h1 class="title">NBA GAME PREDICTOR</h1>
    """

# Exibir o HTML no Streamlit
st.markdown(title_html, unsafe_allow_html=True)


selected_date = st.date_input("Choose the day you want previsions for", date.today())
formatted_date = selected_date.strftime("%m/%d/%Y")

season_id = get_nba_season_id(selected_date)


if st.button("Get predictions"):
    try:
        games = get_schedule(formatted_date,season_id)
        if games:
            for game in games:
                game = add_team_info(game,pd_teams)
                game = add_game_info(game,pd_games,pd_players,season_id,selected_date)
                processed_data = process_input(game)
                prediction=predict(processed_data)
                if prediction == 1:
                    winning_team = game['HOME_TEAM_NAME']
                else:
                    winning_team =game['VISITOR_TEAM_NAME']
                
                visitor_logo = f"{STREAMLIT_LOGOS_DIRECTORY}/{game['VISITOR_TEAM_NAME']}.png"
                home_logo = f"{STREAMLIT_LOGOS_DIRECTORY}/{game['HOME_TEAM_NAME']}.png"

                
                display_team_matchup(
                    visitor_team_name=game['VISITOR_TEAM_NAME'],
                    home_team_name=game['HOME_TEAM_NAME'],
                    visitor_logo_url=visitor_logo,
                    home_logo_url=home_logo,
                    prediction=winning_team
                )
                
        else:
            st.write("No games found for the chosen date")
    except Exception as e:
        st.write("No games found for the chosen date")

# Adicionar o footer com as informações sobre as limitações do modelo de previsão
footer_html = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        color: #333;
    }
    </style>
    <div class="footer">
    Disclaimer: The predictions provided by this model are based on statistical analysis and historical data but do not guarantee a 100% accuracy rate.
    NBA games involve unpredictable variables and events beyond our control.
    Use these predictions as a reference, not as a certainty.
    </div>
    """

# Exibir o footer no Streamlit
st.markdown(footer_html, unsafe_allow_html=True)




