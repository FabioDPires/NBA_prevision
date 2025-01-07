import pandas as pd
from nba_api.stats.static import teams

# Function to get team information
def get_teams_info():
    teams_info = teams.get_teams()
    return teams_info

# Fetch team information
teams_info = get_teams_info()


# Convert to DataFrame
df = pd.DataFrame(teams_info)

# Save the DataFrame to an Excel file
file_name = 'nba_teams.xlsx'
df.to_excel(file_name, index=False)

print(f"Data saved to {file_name}")
