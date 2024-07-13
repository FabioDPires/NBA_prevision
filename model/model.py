import streamlit as st
import requests
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import teams
from nba_api.live.nba.endpoints import scoreboard
from collections import defaultdict
from datetime import date
from datetime import datetime
from nba_api.stats.endpoints import leaguegamefinder
import json

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
                    "game_id": game_id,
                    "vtCity" : game["vtCity"],
                    "visitor_team" :  game["vtNickName"],
                    "htCity" : game["htCity"],
                    "home_team" :  game["htNickName"],
                    "date": game["date"],
                }
                games_array.append(game_info)
                seen_game_ids.add(game_id)
        
        return games_array
    else:
        print(f"Falha ao acessar os dados. Status code: {response.status_code}")
        return None
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
            st.write(f"{game['visitor_team']} @ {game['home_team']}")
    else:
        st.write("No games found for the chosen date")







