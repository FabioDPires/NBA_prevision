import utils
import headers
import details
import merge_headers_lines
import players

SEASON_BEGIN_DATE = '10/22/2024'
START_DATE = '2024-10-22'
END_DATE = '2025-01-07'
SEASON = '2024-25'

utils.clean_previous_data()
#utils.clean_data_folder()

print("Getting games headers")
headers.get_headers(START_DATE,END_DATE)
print("Getting games details")
details.get_games_details(START_DATE,END_DATE)
merge_headers_lines.merge_headers_lines()
print("Getting player details")
players.get_players(SEASON,SEASON_BEGIN_DATE)
