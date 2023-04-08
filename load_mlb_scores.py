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

from beat_the_odds.models import Team, Contest, Game, Pick, Result

# Issue an API call to get the latest odds in JSON format
url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/scores/?apiKey=f13fe3a3f1ea67d9a1c15d549efc719e&daysFrom=1'
r = requests.get(url)
odds_data = r.json()

# For testing purposes, read json data from a file
# filename = 'json/mlb_scores.json'
# with open(filename) as f:
# 	scores_data = json.load(f)

# Get today's date
current_date = datetime.now().date()
# Determine yesterday's date (which will be the contest date)
compare_date = current_date + timedelta(days = -1)

# Process the data returned from the API call
gamelist = []
game_count = 0
error_count = 0
scores_missing = 0
for game in odds_data:
	errors_found = False
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
		error_count += 1
		message = "No match found for team name " + name_away
		logger.error(message)
	else:
		team_away = team.abbrev
	name_home = game['home_team']
	try:
		team = Team.objects.get(name=name_home)
	except:
		errors_found = True
		error_count += 1
		message = "No match found for team name " + name_home
		logger.error(message)
	else:
		team_home = team.abbrev
	if game['scores']:
		score_away = game['scores'][1]['score']
		score_home = game['scores'][0]['score']
		if score_away < score_home:
			outcome_away = 'L'
			outcome_home = 'W'
		elif score_away > score_home:
			outcome_away = "W"
			outcome_home = "L"
		else:
			outcome_away = "T"
			outcome_home = "T"
	else:
		score_away = 0
		score_home = 0
		outcome_away = "T"
		outcome_home = "T"
		scores_missing += 1
		message = "Scores missing for " + team_away + " vs " + team_home + ". Rainout?"
		logger.warning(message)

	if errors_found == True:
		continue

	game_count += 1
	gamedict = {}
	gamedict['game_date'] = game_date
	gamedict['game_time'] = game_time
	gamedict['team_away'] = team_away
	gamedict['team_home'] = team_home
	gamedict['score_away'] = score_away
	gamedict['score_home'] = score_home
	gamedict['outcome_away'] = outcome_away
	gamedict['outcome_home'] = outcome_home
	gamelist.append(gamedict)

if game_count == 0:
	error_count += 1
	message = "No game records found."
	logger.error(message)

league = "MLB"
season = compare_date.strftime("%Y")
period = compare_date.strftime("%b %-d")
try:
	contest = Contest.objects.get(league=league, season=season, period=period)
except:
	error_count += 1
	message = "Contest record not found for " + league + "-" + season + "-" + period
	logger.error(message)

if error_count > 0:
	message = "MLB scores process failed to complete"
	logger.warning(message)
	exit()

for game in gamelist:
	game_date = game['game_date']
	game_time = game['game_time']
	team_away = game['team_away']
	team_home = game['team_home']
	score_away = game['score_away']
	score_home = game['score_home']
	try:
		g = Game.objects.get(contest=contest, team_away=team_away, team_home=team_home)
	except:
		message = "Game record not found for " + team_away + " vs " + team_home
		logger.warning(message)
		continue
	g.score_away = score_away
	g.score_home = score_home
	g.outcome_away = outcome_away
	g.outcome_home = outcome_home
	g.save()

results = Result.objects.filter(contest=contest)
# Tally up the points, wins, losses, and ties for each participant, and
# update their result record accordingly.
for result in results:
	participant = result.participant
	picks = Pick.objects.filter(contest=contest, participant=participant)
	mypicks = []
	for pick in picks:
		mypicks.append(pick.abbrev)
	wins = losses = ties = points = 0
	games = contest.game_set.all().order_by('game_date', 'game_time')
	for game in games:
		if game.team_away in mypicks:
			if game.outcome_away == "W":
				wins += 1
				if game.odds_away > 0:
					points += game.odds_away
				else:
					points += round(-100 / (game.odds_away/100))
			if game.outcome_away == "L":
				losses += 1
				points -= 100
			if game.outcome_away == "T":
				ties += 1
		if game.team_home in mypicks:
			if game.outcome_home == "W":
				wins += 1
				if game.odds_home > 0:
					points += game.odds_home
				else:
					points += round(-100 / (game.odds_home/100))
			if game.outcome_home == "L":
				losses += 1
				points -= 100
			if game.outcome_home == "T":
				ties += 1
	result.wins = wins
	result.losses = losses
	result.ties = ties
	result.points = points
	result.save()
# Determine the winner of the contest
results = Result.objects.filter(contest=contest).order_by("-points")
contest.winner = results[0].participant.username
# Change the status of the contest to "Complete", and send a 
# messsage indicating success.
contest.status = "Complete"
contest.save()

logger.warning("MLB scores process completed successfully")