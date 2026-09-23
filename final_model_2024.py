# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 18:04:44 2024

@author: Jenny
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 20:53:41 2024

@author: Zach
"""

import requests
import random
#import statistics as stats
from matplotlib import pyplot as plt


#getting Team IDs (teamId) and abbreviations (abbr) from conference info
conf_url = 'https://site.api.espn.com/apis/v2/sports/football/college-football/standings'
req = requests.get(conf_url)
conf = req.json()
i = 0
team_abbrs = []
team_Ids_full = []

#%% ESPN API Calls

for ind in conf['children']:
    #SBC is stored differently (nested into divisions) so we have to do something special for them
    if ind['id'] == '37': 
        for div in ind['children']:
            conference = div['standings']
            for team in conference['entries']:
                abbr = team['team']['abbreviation']
                teamId = team['team']['id']
                team_abbrs.append(abbr)
                team_Ids_full.append(teamId)
                print(abbr, ",", teamId)
                i += 1

    else:
        conference = ind['standings']
        for team in conference['entries']:
            abbr = team['team']['abbreviation']
            teamId = team['team']['id']
            team_abbrs.append(abbr)
            team_Ids_full.append(teamId)
            print(abbr, ", ", teamId)
            i += 1

print(i, "FBS teams")

abbrs_Ids = []
for ind in range(len(team_abbrs)):
    abbrs_Ids.append((team_abbrs[ind], team_Ids_full[ind]))

day = input("what day is it? format must be as MM-DD\n")
remaining_games_dict = {}

Wins_dict = {}


for (abbr, teamId) in abbrs_Ids:
    schedule_url = f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{teamId}/schedule?season=2026'
    req = requests.get(schedule_url)
    schedule_info = req.json()
    record_list = schedule_info['team']['recordSummary']
    record_list = record_list.split("-")
    wins = int(record_list[0])
    losses = int(record_list[1]) 
        
    game_list = schedule_info['events']
        #doing a date comparison to extract only games relevant for the rest of the season
    relevant_gameIds = []
    current_gameIds = []
    
    #doing a date comparison to only reference the relevant games
    for game in game_list:
        if int(game['date'][5:7]) > int(day[0:2]):
            relevant_gameIds.append(game['id'])
        

        if int(game['date'][5:7]) == int(day[0:2]):
            if int(game['date'][8:10]) > int(day[3:]):
                relevant_gameIds.append(game['id'])

            #we have to filter between the games happening later today and the games happening now
            if int(game['date'][8:10]) == int(day[3:]):    
                #if game is happening later today, append to relevant_gameIds
                if game['competitions'][0]['status']['period'] == 0:
                    relevant_gameIds.append(game['id'])
                    
                if game['competitions'][0]['status']['period'] != 0:
                #if game is happening now, append to current_gameIds
                    if game['competitions'][0]['status']['type']['completed'] == False:
                        current_gameIds.append(game['id'])
     
    #checking to see if there's any bugs in the relevant_gameId extraction. Some teams don't 
    #play 12 games, so this flags those teams, as well as any other team with something weird going on
    #if ((wins+losses) + len(relevant_gameIds) + len(current_gameIds) != 12):
    if ((wins+losses) + len(relevant_gameIds) + len(current_gameIds) != 12):
        print(abbr, "SCHEDULE ERROR. EITHER A BUG OR THIS TEAM DOESN'T PLAY 12 GAMES")
        print("Games played: ", wins+losses)
        print("Games remaining: ", len(relevant_gameIds))
        if len(current_gameIds) == 1:
            print("Game also happening right now")
    
    
    #this loop checks to see if the games in the relevant_gameIds list are already in the dictionary containing
    #all of the remaining games in CFB this year, then adds them if they aren't
    for game in range(0,len(relevant_gameIds)):
        game_url = f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={relevant_gameIds[game]}'
        req = requests.get(game_url)
        game_info = req.json()
        
        abbr_h, abbr_a = (game_info['boxscore']['teams'][1]['team']['abbreviation'], game_info['boxscore']['teams'][0]['team']['abbreviation'])
        if abbr_h == 'TBD':
            pass
        elif abbr_a == 'TBD':
            pass
        else:
            if (abbr_h, abbr_a) not in remaining_games_dict.keys():
                remaining_games_dict[abbr_h, abbr_a] = float(game_info['predictor']['homeTeam']['gameProjection'])
    
    
    #this loop adds games that are currently happening via their live win probabilities
    if len(current_gameIds) == 1:
        game_url = f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={current_gameIds[0]}'
        req = requests.get(game_url)
        game_info = req.json()
        
        abbr_h, abbr_a = (game_info['boxscore']['teams'][1]['team']['abbreviation'], game_info['boxscore']['teams'][0]['team']['abbreviation'])
        if (abbr_h, abbr_a) not in remaining_games_dict.keys():   
            #if the game just started, it doesn't have the 'winprobability' key yet I think. 
            #we have to check for that first
            if 'winprobability' in game_info.keys():
                remaining_games_dict[abbr_h, abbr_a] = float(game_info['winprobability'][-1]['homeWinPercentage'])
            else: 
                remaining_games_dict[abbr_h, abbr_a] = float(game_info['predictor']['homeTeam']['gameProjection'])
    
    #adding current win totals to the wins_dict
    Wins_dict[abbr] = wins
    
    print(abbr, "DONE!")








#%% FPI Sims
print("Simulating season 100,000 times...(FPI)")
n = 0
mn_avg = []
six_win_bowls = []
seven_win_bowls = []
eight_win_bowls = []

bowl_list_b1g = ['Orlando', 'Tampa', 'Las Vegas', 'Nashville', 'New York', 'Phoenix', 'Other']
Minn_bowl_per_sim = []


#five7list = []
bowlcountlist = []

#tracking total bowl counts, and 5 win bowl counts too
mn_bowlcounts = 0
five_win_bowl = 0 

#Outputs list so we can count different win total separately
win_counts = {i: 0 for i in range(13)}

while n < 100000:
    temp = Wins_dict.copy()

    # Simulate remaining games
    for key in remaining_games_dict:
        randnum = random.random()
        home_prob = remaining_games_dict[key]/100

        if randnum <= home_prob:
            temp[key[0]] += 1  # Home team wins
        else:
            if key[1] in team_abbrs:
                temp[key[1]] += 1  # Away team wins

    wins_list = list(temp.values())
    
    #adds 1 to bowl_countstotal for each team in wins_list with 6+ wins
    bowl_countstotal = sum(1 for x in wins_list if x >= 6)  # Count 6+ win teams
    
    #adds number of wins in sim to mn_avg list, which holds MN only win counts from each simulation
    mn_avg.append(temp['MINN'])
    

    # Here, counts for each 
    temp_wins = temp['MINN']
    if temp_wins in win_counts:
        win_counts[temp_wins] += 1
    
    
    fiveand7_bowl = False
    #Check if MN qualifies for a bowl (6+ wins or 5-win bowl-eligible)    
    if temp_wins >= 6:
        mn_bowlcounts += 1
    elif temp_wins == 5:
        # Check if MN can make a bowl at 5-7 based on APR eligibility
        #adds 1 for each team in that list (high APR teams) that finishes with 5 wins
        Fiveand7_checker = sum(1 for team in ['OSU', 'ALA', 'NU', 'UNC', 'CLEM',
                                              'CIN', 'MICH', 'WIS', 'AFA', 'ND']
                               if temp[team] == 5)
        #five7list.append(Fiveand7_checker)


        '''there are 42 bowls (and 84 bowl slots) for FBS teams. This checks the number of teams
        that get 6+ wins, as well as the number of teams ahead of us in APR that go 5-7, and determines
        whether or not, in a given sim, if we go 5-7, if we would go to a bowl or not 
        (i.e. 84 - bowl eligible - 5-7 teams with higher APR > 0) 
        If we do go to a bowl in this sim, we add to mn_bowlcounts and to five_win_bowl'''        
 
        if (84 - bowl_countstotal - Fiveand7_checker) > 0:
            mn_bowlcounts += 1
            five_win_bowl += 1  #also tracks 5-7 bowl chances too (kind of interesting)
            fiveand7_bowl = True
        
    
    # big ten teams (minus Minnesota for practical purposes)
    b1g_teams = ['IU', 'PSU', 'ILL', 'OSU', 'WIS', 'NEB', 'IOWA', 'MICH', 'MSU', 'MD', 'RUTG', 'NU', 'PUR']
    
    #based on assumption that everyone in the B1G makes the playoff at 11-1 or better but
    #osu, psu, and mich make the playoff at 10-2 most of the time
    playoff_counter = sum(1 for team in b1g_teams if temp[team] >= 11)
    if temp['OSU'] == 10 and playoff_counter < 3:
        playoff_counter += 1
    if temp['PSU'] == 10 and playoff_counter < 3:
        playoff_counter += 1   
    if temp['MICH'] == 10 and playoff_counter < 3:
        playoff_counter += 1
        
        
    
    
    
    # Helper function to calculate team counts based on win condition
    '''why max of 10 (or what? because we're going to eventually subtract our total bigten bowl count by
    3 (one for indexing purposes, 2 because I'm making the assumption that 2 non-oregon teams are going
       to make the playoff). Becuase there's only 7 dedicated bigten bowls, we'd get an indexing error if
    there were more than 10 teams eligible at a given threshold, so in the circumstance that there are 10+ teams bowl eligible, I just set it
    to 10 to assume we go to an 'Other'/non-B1G bowl '''
    
    def calculate_b1g_counts(win_threshold, teams):
        return min(8 + playoff_counter, sum(1 for team in teams if temp[team] >= win_threshold))
    
    # Calculate number of teams with various win thresholds
    ''' why set the minimum to 3 (or whatever the playoff counter is)? because, 
    same as before, we get indexing issues if there's less than 3 in each case'''
    b1g_all = calculate_b1g_counts(6, b1g_teams)  # Teams with 6+ wins
    b1g_7plus = max(playoff_counter + 1, calculate_b1g_counts(7, b1g_teams))
    b1g_8plus = max(playoff_counter + 1, calculate_b1g_counts(8, b1g_teams))
    b1g_9plus = max(playoff_counter + 1, calculate_b1g_counts(9, b1g_teams))  
    b1g_10plus = max(playoff_counter + 1, calculate_b1g_counts(10, b1g_teams))
    # Append bowl based on win count
    if temp_wins == 5:
        if fiveand7_bowl == True: 
            # Assuming 2 non-Oregon B1G schools make the playoff most of the time, so we subtract 3 for indexing
            #also caps at 7 for indexing purposes
            Minn_bowl_per_sim.append(bowl_list_b1g[min(6,b1g_all - 3)])
        else:
            Minn_bowl_per_sim.append("None")
            
    elif 6 <= temp_wins <= 10: 
        # General case for win counts from 6 to 10 (<-- new addition this year)
        # assigns a bowl game based on the number of wins we have and our bowl location assumptions
            
        b1g_win_dict = {6: b1g_all, 7: b1g_7plus, 8: b1g_8plus, 9: b1g_9plus, 10: b1g_10plus}

        #you can modify this list however you want, I think that Michigan, Wisco, and Iowa
        #are all teams that could jump us if they're within one game of us UNLESS they have only 6 wins
        #below bowl == the number of teams per sim that have 1 less win than us that end
        #up going to a better bowl than us anyways
        below_bowl = sum(1 for team in ['MICH'] if temp_wins - temp[team] == 1)
        if temp['MICH'] == 6:
            below_bowl = 0
        
        bowl_index = min(6, b1g_win_dict[temp_wins] - (playoff_counter + 1) + below_bowl)
        
        
        
        #adding a possibility of making the playoff should we win 10 games (and there not be a lot of other b1g teams that make the playoff)
        if temp_wins == 10:
            if playoff_counter <= 1:
                Minn_bowl_per_sim.append('Playoff')
            else:
                Minn_bowl_per_sim.append(bowl_list_b1g[bowl_index])
        else:
            Minn_bowl_per_sim.append(bowl_list_b1g[bowl_index])


    elif temp_wins >= 11:
        Minn_bowl_per_sim.append('Playoff')
        
    else:
        Minn_bowl_per_sim.append("None")
    

    bowlcountlist.append(bowl_countstotal)

    if n % 10000 == 0:
        print(n/1000, "% Done!", sep = "")

    n += 1



#Calculate probabilities
total_simulations = n
win_probabilities = {key: val / total_simulations for key, val in win_counts.items()}
bowl_probability = mn_bowlcounts / total_simulations

#Results
print("\nMINN Season Win Probabilities:")
for win, prob in win_probabilities.items():
    print(f"{win} wins: {prob}")

print("Bowl Probability Added via 5-win bowl seasons:", five_win_bowl / total_simulations)
print("Overall Bowl Probability (6+ wins or 5-win bowl):", bowl_probability)
#print(":)")
#print("\nLikelihood, if we go 5-7, that we'll still go to bowl:", five_win_bowl / win_counts[5])



''' Assumptions for the bowl calculator: 
        Assumes at least 2 teams from the old big ten will make the playoff this year
        Assumes that, should we be tied in record with other teams, that we'll be picked last
        (means that some bowls are super underrepresented, especially new york and phoenix I think)'''

# Printing results of bowl calc
MN_bowl_locs = {
    'Playoff': 0,
    'Orlando': 0,
    'Tampa': 0,
    'Las Vegas': 0,
    'Nashville': 0,
    'New York': 0,
    'Phoenix': 0,
    'Other': 0,
    'None': 0
}

# Count occurrences of each location
for x in Minn_bowl_per_sim:
    if x in MN_bowl_locs:
        MN_bowl_locs[x] += 1

# Calculate and print the odds
print("\nCFB Playoff odds: ", MN_bowl_locs['Playoff'] / total_simulations)
print("\nOrlando odds: ", MN_bowl_locs['Orlando'] / total_simulations)
print("Tampa odds: ", MN_bowl_locs['Tampa'] / total_simulations)
print("Las Vegas odds: ", MN_bowl_locs['Las Vegas'] / total_simulations)
print("Nashville odds: ", MN_bowl_locs['Nashville'] / total_simulations)
print("New York odds: ", MN_bowl_locs['New York'] / total_simulations)
print("Phoenix odds: ", MN_bowl_locs['Phoenix'] / total_simulations)
print("Detroit odds: RIP :(")
print("Other bowl odds: ", MN_bowl_locs['Other'] / total_simulations)
print("\nNo Bowl odds: ", MN_bowl_locs['None'] / total_simulations)










#%% Histograms
''' HISTOGRAMS '''
#Histogram for bowl eligible teams
# plt.hist(bowlcountlist, bins=range(min(bowlcountlist), max(bowlcountlist) + 2),
#           color='gold', edgecolor='maroon')

# plt.xlabel('# of bowl eligible teams')
# plt.ylabel('Frequency (n = 100,000)')
# plt.savefig('bowl_eligible_teams.png', format='png', dpi=300, bbox_inches='tight')


# plt.clf()
# #Histogram of MN wins
plt.hist(mn_avg, bins=range(min(mn_avg), max(mn_avg) + 2),
          color='gold', edgecolor='maroon', density = True)

plt.xlabel('# of wins')
plt.ylabel('Frequency % (n = 100,000)')
plt.savefig('mn_season_sims.png', format='png', dpi=300, bbox_inches='tight')
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}'.format(y * 100)))



# bowl Locs histogram
keys = list(MN_bowl_locs.keys())
values = [v / 1000 for v in MN_bowl_locs.values()]
x_pos = range(len(keys))
plt.bar(x_pos, values, color='gold', edgecolor='maroon')
plt.xticks(x_pos, keys, rotation = 45)
plt.xlabel("Bowls")
plt.ylabel("Frequency % (n = 100,000)")



