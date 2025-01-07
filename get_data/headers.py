import pandas as pd
from nba_api.stats.endpoints import scoreboardv2
import time

def get_all_game_headers(start_date,end_date):
    game_headers = []
    
    # Lista de datas para a temporada
    date_range = pd.date_range(start=start_date, end=end_date)

    for date in date_range:
        print(f"Buscando jogos em {date.strftime('%Y-%m-%d')}...")
        attempts = 0
        
        while attempts < 3:  # Tenta até 3 vezes
            try:
                scoreboard = scoreboardv2.ScoreboardV2(
                    game_date=date.strftime('%Y-%m-%d'),
                    timeout=60
                )
                games = scoreboard.get_normalized_dict()['GameHeader']
                game_headers.extend(games)
                print(f"Encontrados {len(games)} jogos.")
                break  # Sai do loop se a busca for bem-sucedida
            except Exception as e:
                attempts += 1
                print(f"Erro ao buscar jogos em {date.strftime('%Y-%m-%d')}: {e}")
                time.sleep(2)  # Espera 2 segundos antes da próxima tentativa
        
        time.sleep(1)  # Espera 1 segundo entre as requisições

    return game_headers

def get_headers(start_date,end_date):
    # Exemplo de uso
    game_headers = get_all_game_headers(start_date,end_date)
    df_game_headers = pd.DataFrame(game_headers)
    df_game_headers.to_excel('headers.xlsx', index=False)
