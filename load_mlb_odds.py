import os
import django
import logging
import requests
import json
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger("beat_the_odds.views")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faganweb.settings')
django.setup()

from beat_the_odds.models import Team, Contest, Game

# Issue an API call to get the latest odds in JSON format
url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey=f13fe3a3f1ea67d9a1c15d549efc719e&bookmakers=fanduel&markets=h2h&oddsFormat=american'
r = requests.get(url)
odds_data = r.json()

# For testing purposes, read json data from a file
# filename = 'json/mlb_odds.json'
# with open(filename) as f:
# 	odds_data = json.load(f)

# Get today's date
current_date = datetime.now().date()
# Determine tomorrow's date (which will be the contest date)
# compare_date = current_date
compare_date = current_date + timedelta(days = 1)

# Process the data returned from the API call
gamelist = []
errors_found = False
game_count = 0
for game in odds_data:
	game_datetime_UTC = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
	game_datetime_ET = game_datetime_UTC.astimezone(ZoneInfo("America/New_York"))
	game_date = game_datetime_ET.date()
	game_time = game_datetime_ET.time()
	if game_date != compare_date:
		continue
	name_away = game['away_team']
	try:
		team = Team.objects.get(name=name_away)
	except:
		errors_found = True
		message = "No match found for team name " + name_away
		logger.error(message)
	else:
		team_away = team.abbrev
	name_home = game['home_team']
	try:
		team = Team.objects.get(name=name_home)
	except:
		errors_found = True
		message = "No match found for team name " + name_home
		logger.error(message)
	else:
		team_home = team.abbrev
	odds_away = game['bookmakers'][0]['markets'][0]['outcomes'][1]['price']
	odds_home = game['bookmakers'][0]['markets'][0]['outcomes'][0]['price']
	if odds_away == None or odds_home == None:
		errors_found = True
		message = "Odds not yet posted for " + team_away + " vs " + team_home

	if errors_found == True:
		continue

	game_count += 1
	gamedict = {}
	gamedict['game_date'] = game_date
	gamedict['game_time'] = game_time
	gamedict['team_away'] = team_away
	gamedict['team_home'] = team_home
	gamedict['odds_away'] = odds_away
	gamedict['odds_home'] = odds_home
	gamelist.append(gamedict)

if game_count < 10:
	errors_found =True
	message = "Need 10 or more games. Only " + game_count + " were found."
	logger.error(message)

league = "MLB"
season = compare_date.strftime("%Y")
period = compare_date.strftime("%b %-d")
contest = Contest.objects.filter(league=league, season=season, period=period)
if len(contest) > 0:
	errors_found = True
	message = "A contest record already exists for " + league + "-" + season + "-" + period
	logger.error(message)

if errors_found == True:
	message = "MLB odds process failed to complete"
	logger.warning(message)
	exit()

c = Contest(league= league, season=season, period=period, num_picks=5, status="Active")
c.save()

for game in gamelist:
	game_date = game['game_date']
	game_time = game['game_time']
	team_away = game['team_away']
	team_home = game['team_home']
	odds_away = game['odds_away']
	odds_home = game['odds_home']
	g = Game(contest=c, game_date=game_date, game_time=game_time, team_away=team_away, team_home=team_home, \
		odds_away=odds_away, odds_home=odds_home)
	g.save()


logger.warning("MLB odds process completed successfully")



