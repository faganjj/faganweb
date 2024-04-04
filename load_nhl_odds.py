import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faganweb.settings')

django.setup()

import logging
logger = logging.getLogger("faganweb scripts")

import requests
import json
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum
from django_apscheduler.models import DjangoJobExecution
from operator import itemgetter

from django.conf import settings

from beat_the_odds.models import Contest, Team, Game, Result, Pick, User


def load_nhl_scores():
	""" This script runs in the morning after a day of NHL games.  It updates the scores of the games, and tallies the results
    	of all users who participated in the day's contest """

	# Issue an API call to get the latest scores in JSON format
	SPORT = "icehockey_nhl"
	API_KEY = "f13fe3a3f1ea67d9a1c15d549efc719e"
	url = 'https://api.the-odds-api.com/v4/sports/' + SPORT + '/scores/?apiKey=' + API_KEY + '&daysFrom=2'
	r = requests.get(url)
	scores_data = r.json()

	# For testing purposes, read json data from a file
	# filename = 'json/mlb_scores.json'
	# with open(filename) as f:
	# 	scores_data = json.load(f)

	# Get today's date
	current_date = datetime.now().date()
	# Determine YESTERDAY's date (which will be the contest date)
	compare_date = current_date + timedelta(days = -1)

	# Process the data returned from the API call
	gamelist = []
	game_count = 0
	error_found = False
	# Use the scores-missing variable to keep track of games for which scores have not been posted,
	# likely because the game was rained-out, or suspended for some other reason.
	scores_missing = 0
	for game in scores_data:
		game_error_found = False

		game_id = game['id']
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
			game_error_found = True
			error_found = True
			message = "No match found for team name " + name_away
			logger.error(message)
		else:
			team_away = team.abbrev
		name_home = game['home_team']
		try:
			team = Team.objects.get(name=name_home)
		except:
			game_error_found = True
			error_found = True
			message = "No match found for team name " + name_home
			logger.error(message)
		else:
			team_home = team.abbrev

		# Use the "scores" key in the API data to get the scores for the away and home teams.
		if game['scores']:
			if game['scores'][0]['name'] == name_away:
				score_away = int(game['scores'][0]['score'])
				score_home = int(game['scores'][1]['score'])
			else:
				score_away = int(game['scores'][1]['score'])
				score_home = int(game['scores'][0]['score'])

			# Based on the scores, determine the outcome for each game (Win, Lose, or Tie)	
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
			# If no scores were found for this game, treat is as a 0-0 tie, and log a warning
			# message to the console.
			score_away = 0
			score_home = 0
			outcome_away = "T"
			outcome_home = "T"
			scores_missing += 1
			message = "Scores missing for " + team_away + " vs " + team_home + ". Rainout?"
			logger.warning(message)

		if game_error_found == True:
			continue

		game_count += 1
		gamedict = {}
		gamedict['game_id'] = game_id
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
		error_found == True
		message = "No game records found."
		logger.error(message)

	# Get the Contest record for the recently completed contest (yesterday for MLB, 
	# the prior weekend for NFL).  If no Contest record found, log an error message
	# and terminate the process.
	league = "NHL"
	season = compare_date.strftime("%Y")
	period = compare_date.strftime("%b %-d")
	try:
		contest = Contest.objects.get(league=league, season=season, period=period)
	except:
		error_found = True
		message = "Contest record not found for " + league + "-" + season + "-" + period
		logger.error(message)

	if error_found == True:
		message = "NHL scores process failed to complete"
		logger.warning(message)
		return

	# For each game in gamelist, update the corresonding Game record, populating it with the scores
	# and outcomes. 
	for game in gamelist:
		game_id = game['game_id']
		game_time = game['game_time']
		team_away = game['team_away']
		team_home = game['team_home']
		score_away = game['score_away']
		score_home = game['score_home']
		outcome_away = game['outcome_away']
		outcome_home = game['outcome_home']
		try:
			g = Game.objects.get(contest=contest, team_away=team_away, team_home=team_home, game_id=game_id)
		except:
			# If the game record does not exist, log a warning message.  This is likely because odds
			# for this game had not been posted in time, so it was not included in the contest.
			message = "Game record not found for " + team_away + " vs " + team_home
			logger.warning(message)
			continue
		g.score_away = score_away
		g.score_home = score_home
		g.outcome_away = outcome_away
		g.outcome_home = outcome_home
		g.save()

	# Now process the Game records in the database to see if any games were missing from odds_data
	# (another potential indicator of a game that may have been suspended for rain or some other reason)
	games = contest.game_set.all().order_by('game_date', 'game_time')
	for game in games:
		# Check if a game has an outcome of None
		if game.outcome_away == "" and game.outcome_home == "":
			# Treat the game as a 0-0 tie
			game.score_away = 0
			game.score_home = 0
			game.outcome_away = "T"
			game.outcome_home = "T"
			game.save()
			scores_missing += 1
			message = "Scores missing for " + game.team_away + " vs " + game.team_home + ". Rainout?"
			logger.warning(message)

	# If no picks were made for the contest, log a message and terminate the process.
	results = Result.objects.filter(contest=contest)
	if len(results) == 0:
		message = "There were no picks for the " + period + " contest."
		logger.warning (message)
		logger.info("MLB scores process completed successfully")
		return

	# Tally up the points, wins, losses, and ties for each participant, and
	# update their result record accordingly.
	for result in results:
		participant = result.participant
		picks = Pick.objects.filter(contest=contest, participant=participant).order_by('-time_stamp')[:contest.num_picks]
		wins = losses = ties = points = 0
		games = contest.game_set.all().order_by('game_date', 'game_time')
		for game in games:
			for pick in picks:
				if game.outcome_away == "W" and game.team_away == pick.abbrev and game.game_id == pick.game_id:
					wins += 1
					if game.odds_away > 0:
						points += game.odds_away
					else:
						points += round(-100 / (game.odds_away/100))
				if game.outcome_away == "L" and game.team_away == pick.abbrev and game.game_id == pick.game_id:
					losses += 1
					points -= 100
				if game.outcome_away == "T" and game.team_away == pick.abbrev and game.game_id == pick.game_id:
					ties += 1
				if game.outcome_home == "W" and game.team_home == pick.abbrev and game.game_id == pick.game_id:
					wins += 1
					if game.odds_home > 0:
						points += game.odds_home
					else:
						points += round(-100 / (game.odds_home/100))
				if game.outcome_home == "L" and game.team_home == pick.abbrev and game.game_id == pick.game_id:
					losses += 1
					points -= 100
				if game.outcome_home == "T" and game.team_home == pick.abbrev and game.game_id == pick.game_id:
					ties += 1
		result.wins = wins
		result.losses = losses
		result.ties = ties
		result.points = points
		result.save()
	# Determine the winner of the contest and update the winner field in the Contest record.
	results = Result.objects.filter(contest=contest).order_by("-points")
	contest.winner = results[0].participant.username
	# Change the status of the contest to "Complete", and send a 
	# messsage indicating success.
	contest.status = "Complete"
	contest.save()

	logger.info("NHL scores process completed successfully")


load_nhl_scores()

