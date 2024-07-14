import streamlit as st
import requests
from collections import defaultdict
from datetime import date
from datetime import datetime
import json
import pandas as pd

SEASON_ID=2023

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

    visitor_team_info = teams.loc[teams['nickname'] == game['VISITOR_TEAM_NAME'], ['id', 'year_founded']]
    if not visitor_team_info.empty:
        visitor_team_id = visitor_team_info['id'].values[0]
        visitor_team_foundation = visitor_team_info['year_founded'].values[0]
    else:
        visitor_team_id = None
        visitor_team_foundation = None

    game['HOME_TEAM_ID'] = home_team_id
    game['FOUNDATION_HOME'] = home_team_foundation
    game['VISITOR_TEAM_ID'] = visitor_team_id
    game['FOUNDATION_VISITOR'] = visitor_team_foundation
    
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

    return total_games, total_wins, total_losses, win_percentage


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


def add_game_info(game, pd_games, season_id, selected_date):
    selected_date = pd.to_datetime(selected_date)
    pd_games['GAME_DATE_EST'] = pd.to_datetime(pd_games['GAME_DATE_EST'])
    pd_games_sorted = pd_games.sort_values(by='GAME_DATE_EST')

    #HOME TEAM
    home_team_id = game["HOME_TEAM_ID"]
    home_stats = calculate_team_stats(home_team_id, pd_games, season_id, selected_date)
    game['HOME_TEAM_TOTAL_GAMES'], game['HOME_TEAM_TOTAL_WINS'], game['HOME_TEAM_TOTAL_LOSSES'], game['HOME_TEAM_WIN_PERCENTAGE'] = home_stats

    home_stats_at_home=calculate_team_stats_at_home(home_team_id,pd_games,season_id,selected_date)
    game['HOME_TEAM_TOTAL_LOSSES_AT_HOME'], game['HOME_TEAM_WIN_PERCENTAGE_AT_HOME'],game['HOME_TEAM_WIN/LOSS_STREAK_AT_HOME'] = home_stats_at_home


    #AWAY TEAM
    visitor_team_id = game["VISITOR_TEAM_ID"]
    visitor_stats = calculate_team_stats(visitor_team_id, pd_games, season_id, selected_date)
    game['VISITOR_TEAM_TOTAL_GAMES'], game['VISITOR_TEAM_TOTAL_WINS'], game['VISITOR_TEAM_TOTAL_LOSSES'], game['VISITOR_TEAM_WIN_PERCENTAGE'] = visitor_stats

    visitor_stats_away = calculate_team_stats_away(visitor_team_id,pd_games,season_id,selected_date)
    game['AWAY_TEAM_WIN_PERCENTAGE_AWAY'] = visitor_stats_away
    return game


pd_teams = pd.read_excel('data/nba_teams.xlsx')
pd_games = pd.read_excel('data/games.xlsx')



# Título da aplicação
st.title("NBA GAME PREDICTOR")

# Widget de entrada de data
selected_date = st.date_input("Choose the day you want previsions for", date.today())
formatted_date = selected_date.strftime("%m/%d/%Y")

season_id = get_nba_season_id(selected_date)

if st.button("Get previsions"):
    games = get_schedule(formatted_date,season_id)
    if games:
        for game in games:
            game = add_team_info(game,pd_teams)
            game = add_game_info(game,pd_games,season_id,selected_date)
            st.write(f"{game['VISITOR_TEAM_NAME']} @ {game['HOME_TEAM_NAME']}")
    else:
        st.write("No games found for the chosen date")







