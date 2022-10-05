import requests
import json
import pandas as pd
import datetime as dt
import time

""" Setting these values so they exist for the f-string """

# fixed values
pg_size = 40 # max value of 40, doesn't go past that
boss_id = 1 # zamorak

# values to be iterated over
grp_size = 1
pg_no = 0

player_dict = {} # player_name : combined enrage

for grp_size in range(1,6):
    players_added = [] # adds the player to this list so only their highest enrage counts (will check against this list each time)
    for pg_no in range(0,8): # page number range, they start with 0
        try:
            response = requests.get(f"https://secure.runescape.com/m=group_hiscores/v1//groups?groupSize={grp_size}&size={pg_size}&bossId={boss_id}&page={pg_no}").text
            print(response)
        except:
            print("Invalid response.")
            break

        while "<title>Error - RuneScape | Old School RuneScape</title>" in response:
            response = requests.get("https://secure.runescape.com/m=news/")
            time.sleep(5)
            response = requests.get(f"https://secure.runescape.com/m=group_hiscores/v1//groups?groupSize={grp_size}&size={pg_size}&bossId={boss_id}&page={pg_no}").text
            time.sleep(5)

        time.sleep(1)

        json_data = json.loads(response)
        player_info = json_data['content'] # list of dictionaries, each dict being an entry (ie a team)
        # print(player_info)
        for team in player_info:
            team_enr = team['enrage']
            for player in team['members']:
                player_name = player['name'].replace(u'\xa0', u' ') # finds the player name and replaces the \xa0 character with a space
                if player_name in players_added: # ensures each player is only added once per group size
                    continue
                if player_name in player_dict:
                    player_dict[f"{player_name}"] += team_enr
                else:
                    player_dict[f"{player_name}"] = team_enr
                players_added.append(player_name)
        print(f"grp_size: {grp_size}, pg_no: {pg_no}")

""" Creating a list of (name, enrage) tuples """
player_data_list = []

for key in sorted(player_dict, key=player_dict.get, reverse=True):
    player_data_pair = (key, player_dict[key])
    player_data_list.append(player_data_pair)

player_df = pd.DataFrame(player_data_list, columns=['Name', 'Combined Enrage'])
print(player_df)

current_time = dt.datetime.today().strftime("%Y-%M-%d %H-%M-%S")

player_csv = player_df.to_csv(f'Combined Zamorak Enrage Hiscores - {current_time}.csv', index=False)