"""
Goal: Determine the fastest kill per 50 enrage interval (eg 0-49 enr, 250-299 enr etc) for each group size.
Then plot the data on a graph, with each of the 5 group sizes
And store the data in a local csv file
"""

import requests
import json
import pandas as pd
import datetime as dt
import time
import math
import matplotlib.pyplot as plt

min_enr = 100 # minimum enrage to check

# fixed values
pg_size = 40 # max value of 40, doesn't go past that
boss_id = 1 # boss_id 1 = zamorak

grp_size = 1 # I think this might be redundant
pg_no = 0 # inital value for the while loop on line 32

""" Min and max group sizes to look at"""
min_grp_size = 1
max_grp_size = 5

kills_info_list = []
for grp_size in range(min_grp_size,max_grp_size+1):
    players_added = [] # adds the player to this list so only their highest enrage counts (will check against this list each time)
    recent_enr = None
    while recent_enr == None or recent_enr > min_enr:
        try:
            response = requests.get(f"https://secure.runescape.com/m=group_hiscores/v1//groups?groupSize={grp_size}&size={pg_size}&bossId={boss_id}&page={pg_no}").text
        except:
            print("Invalid response.")
            break

        while "<title>Error - RuneScape | Old School RuneScape</title>" in response:
            print("Still error...")
            time.sleep(5)
            response = requests.get("https://secure.runescape.com/m=news/")
            time.sleep(5)
            response = requests.get(f"https://secure.runescape.com/m=group_hiscores/v1//groups?groupSize={grp_size}&size={pg_size}&bossId={boss_id}&page={pg_no}").text

        print(response)
        time.sleep(1)

        json_data = json.loads(response)
        player_info = json_data['content'] # list of dictionaries, each dict being an entry (ie a team)
        # print(player_info)

        for team in player_info:
            team_enr = team['enrage']
            kill_time = math.floor(team['killTimeSeconds'])
            players = [player["name"].replace(u'\xa0', u' ') for player in team['members']]

            kill_info = [grp_size, team_enr, kill_time, players]
            kills_info_list.append(kill_info)

        recent_enr = team_enr
        print(f"grp_size: {grp_size}, pg_no: {pg_no}")
        pg_no += 1
    pg_no = 0  # recents pg_no to 0 for the next group size

# print(kills_info_list)
# print(len(kills_info_list))

refined_data = [] # filtering so only fastest per enr is shown
for i in range(len(kills_info_list)):
    if i == 0:
        refined_data = [kills_info_list[i]]
    elif kills_info_list[i][1] == kills_info_list[i-1][1]: # if this entry's enrage is the same as the previous one's
        continue
    else:
        refined_data.append(kills_info_list[i])

print(refined_data)
# print(len(refined_data))

""" Pandas preferences, can ignore. Only doing this so I can see the full dataframe in pycharm"""

pd.options.display.width= None
pd.options.display.max_columns= None
pd.set_option('display.max_rows', 300)
pd.set_option('display.max_columns', 300)

""" Full kills data as a DataFrame (fastest kills for each enrage, per group size) """

kills_df = pd.DataFrame(refined_data, columns=['group_size', 'enrage', 'kill_time', 'players'])
print(kills_df)

""" 
Determining the fastest kill per 50 enrage interval (eg 150-199%)
Separating it into 5 dictionaries - each representing a different group size

Iterating over all group sizes (1-5)
"""

all_data_dict = {}
for grp_size in range(min_grp_size,max_grp_size+1):
    
    group_size_dict = {} # going to fill this with the fastest times for each enrage interval (eg fastest for 100-149, 250-299 etc)
    group_size_filter = (kills_df['group_size'] == grp_size)
    df_group_size = kills_df.loc[group_size_filter]
    # print(df_group_size)

    group_best_kills = {}
    # print("here we go...")
    i = 0
    while i * 50 <= df_group_size['enrage'].max(axis=0): # iterate until we hit the base minimum value
        enr_filter = (df_group_size['enrage'] >= i * 50) & (df_group_size['enrage'] < (i+1) * 50)
        group_best_kills[f"{i*50}-{(i+1)*50-1}"] = None
        for row in df_group_size.loc[enr_filter].itertuples():
            # print(row.enrage, row.kill_time)
            if group_best_kills[f"{i*50}-{(i+1)*50-1}"] == None:
                group_best_kills[f"{i * 50}-{(i + 1) * 50 - 1}"] = row.kill_time
                # print(f"Fastest -- {i * 50}-{(i + 1) * 50 - 1}")
            elif row.kill_time < group_best_kills[f"{i * 50}-{(i + 1) * 50 - 1}"]:
                group_best_kills[f"{i * 50}-{(i + 1) * 50 - 1}"] = row.kill_time
                # print(f"Fastest -- {i * 50}-{(i + 1) * 50 - 1}")
            # else:
            #     print("too slow")

        i += 1 # increases the enrage to iterate over

        all_data_dict[f"{grp_size}"] = group_best_kills

    # print(f"Group size {grp_size}\n {group_best_kills}")

print(all_data_dict)

full_enrages_dict = {}
for group_size, enrages_dict in all_data_dict.items():
    data_pairs = []
    for enrage_range, killtime in enrages_dict.items():
        if killtime != None:
            if enrage_range == '0-49' or enrage_range == '50-99': # if it's either of these, [:3] will break
                continue
            elif enrage_range.find('-') != -1: # if a dash is found
                dash_position = enrage_range.find('-')
                data_pair = [int(enrage_range[:dash_position]), killtime]  # dash_position determines how many digits to extract
                data_pairs.append(data_pair)
    full_enrages_dict[f"{group_size}"] = data_pairs

print(full_enrages_dict)

""" Saving to local CSV file """

current_time = dt.datetime.today().strftime("%Y-%M-%d %H-%M-%S")

kills_csv = kills_df.to_csv(f'Fastest Kill times per Max Enrage - {current_time}.csv', index=False)

""" Graphing """

for group_size in range(1,6):
    pairs = full_enrages_dict[f"{group_size}"] # narrows it down to the group size

    enrages = [x[0] for x in pairs] # enrages are the first values in each data pair
    killtimes = [x[1]/60 for x in pairs] # kill times are the second values in each data pair

    plt.plot(enrages, killtimes, label=f"Group Size {group_size}", linestyle='--')

plt.xlabel("Max Enrage (%)")
plt.ylabel("Kill Time (min)")
plt.xlim(left=min_enr) # setting the minimum x value
plt.legend()
plt.show()