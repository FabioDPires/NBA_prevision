import pandas as pd

def remove_extra_columns(headers):
    columns_to_remove = [
    "GAME_SEQUENCE",
    "GAME_STATUS_ID",
    "GAME_STATUS_TEXT",
    "LIVE_PERIOD",
    "LIVE_PC_TIME",
    "NATL_TV_BROADCASTER_ABBREVIATION",
    "HOME_TV_BROADCASTER_ABBREVIATION",
    "AWAY_TV_BROADCASTER_ABBREVIATION",
    "LIVE_PERIOD_TIME_BCAST",
    "ARENA_NAME",
    "WH_STATUS",
    "WNBA_COMMISSIONER_FLAG"
    ]

    headers = headers.drop(columns=columns_to_remove)
    return headers

def merge_headers_lines():

    headers = pd.read_excel('headers.xlsx')
    line = pd.read_excel('line_scores.xlsx')

    ######################POINTS###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'PTS']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['PTS_home'] = headers['PTS']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('PTS', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'PTS']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['PTS_away'] = headers['PTS']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('PTS', axis=1, inplace=True)

    ######################ASSISTS###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'AST']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['AST_home'] = headers['AST']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('AST', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'AST']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['AST_away'] = headers['AST']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('AST', axis=1, inplace=True)

    ######################REB###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'REB']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['REB_home'] = headers['REB']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('REB', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'REB']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['REB_away'] = headers['REB']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('REB', axis=1, inplace=True)

    ######################FG_PCT###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FG_PCT']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FG_PCT_home'] = headers['FG_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FG_PCT', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FG_PCT']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FG_PCT_away'] = headers['FG_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FG_PCT', axis=1, inplace=True)

    ######################FT_PCT###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FT_PCT']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FT_PCT_home'] = headers['FT_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FT_PCT', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FT_PCT']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FT_PCT_away'] = headers['FT_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FT_PCT', axis=1, inplace=True)

    ######################FG3_PCT###########################
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FG3_PCT']], left_on=['GAME_ID','HOME_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FG3_PCT_home'] = headers['FG3_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FG3_PCT', axis=1, inplace=True)
        
    headers = headers.merge(line[['GAME_ID','TEAM_ID', 'FG3_PCT']], left_on=['GAME_ID','VISITOR_TEAM_ID'], right_on=['GAME_ID','TEAM_ID'], how='left')
    headers['FG3_PCT_away'] = headers['FG3_PCT']
    headers.drop('TEAM_ID', axis=1, inplace=True)
    headers.drop('FG3_PCT', axis=1, inplace=True)

    headers['FG_PCT_home'] = headers['FG_PCT_home'].round(3)
    headers['FG_PCT_away'] = headers['FG_PCT_away'].round(3)
    headers['FT_PCT_home'] = headers['FT_PCT_home'].round(3)
    headers['FT_PCT_away'] = headers['FT_PCT_away'].round(3)
    headers['FG3_PCT_home'] = headers['FG3_PCT_home'].round(3)
    headers['FG3_PCT_away'] = headers['FG3_PCT_away'].round(3)

    headers=remove_extra_columns(headers)

    headers['HOME_TEAM_WINS'] = (headers['PTS_home'] > headers['PTS_away']).astype(int)

    headers.to_excel('games.xlsx', index=False)