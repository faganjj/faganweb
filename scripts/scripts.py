
###  LOAD_MLB_ODDS  ###

import os
import django

# The following statements allow the django ORM to be used in scripts.  It accesses the settings.py file for faganweb.
# Here's a link to a video that explains it:
# https://www.google.com/search?
#	q=use+django+orm+in+python+script&rlz=1C5CHFA_enUS897US897&oq=use+django+orm+in+python+script
#	&aqs=chrome..69i57j0i390i650l4j69i60.33598j1j7&sourceid=chrome&ie=UTF-8#fpstate=ive&vld=cid:0c8bffb5,vid:AS01VoC9l5w
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faganweb.settings')
#django.setup()

import logging
logger = logging.getLogger("faganweb scripts")

import requests
import json
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum
from django_apscheduler.models import DjangoJobExecution

from django.conf import settings

from beat_the_odds.models import Contest, Team, Game, Result, Pick, User, OddsCount

def load_mlb_odds():



	# Temporary logic to assess how early different Bookmakers are posting their odds
	url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey=f13fe3a3f1ea67d9a1c15d549efc719e&regions=us&markets=h2h&oddsFormat=american'
	r = requests.get(url)
	odds_data = r.json()	
	curr_date = datetime.now().date()
	curr_time = datetime.now().time()
	current_date = datetime.now().date()
	compare_date = current_date + timedelta(days = 1)
	b_list = []
	for game in odds_data:
		game_datetime_UTC = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
		# Convert the UTC date/time to Eastern time.  All times in Beat the Odds are in Eastern time.
		game_datetime_ET = game_datetime_UTC.astimezone(ZoneInfo("America/New_York"))
		# Separate the date/time into two variables, one for date and one for time.
		game_date = game_datetime_ET.date()
		# If the game date is not equal to the contest date, skip this game and proceed to the next.
		if game_date != compare_date:
			continue
		if game['bookmakers']:
			bookmakers = game['bookmakers']
			for bookmaker in bookmakers:
				name = bookmaker['key']
				found = False
				for d in b_list:
					if d['name'] == name:
						found = True
						count = d['count']
						count += 1
						d['count'] = count
				if found == False:
					new_entry = {'name': name, 'count': 1}
					b_list.append(new_entry)
	for d in b_list:
		name = d['name']
		count = d['count']
		odds = OddsCount(date=curr_date, time=curr_time, name=name, count=count)
		odds.save()
	logger.info("Odds assessment completed")





	# Issue an API call to get the latest odds in JSON format.  the-odds-api.com is being used as the data source.
	SPORT = "baseball_mlb"
	# BOOKMAKER = "fanduel"
	# API_KEY = "f13fe3a3f1ea67d9a1c15d549efc719e"
	BOOKMAKER = os.getenv('BOOKMAKER')
	API_KEY = os.getenv('API_KEY')
	url = 'https://api.the-odds-api.com/v4/sports/'+ SPORT + '/odds/?apiKey=' + API_KEY + '&bookmakers=' + BOOKMAKER + '&markets=h2h&oddsFormat=american'
	r = requests.get(url)
	odds_data = r.json()

	# For testing purposes, read json data from a file
	# filename = 'json/mlb_odds.json'
	# with open(filename) as f:
	# 	odds_data = json.load(f)

	# Get today's date and time
	current_date = datetime.now().date()
	current_time = datetime.now().time()

	# Determine tomorrow's date (which will be the contest date)
	# compare_date = current_date
	compare_date = current_date + timedelta(days = 1)

	# Establish a time_of-day deadline for running the script on a particular day.  When the spript runs prior to 
	# the deadline, it will fail if odds for one or more games have not yet been posted.  But when it runs after
	# the deadline, it will accept and process all games for which odds have been posted by that time.
	# For now, the deadline is 10:00 PM.
	deadline = time(22, 0, 0)

	# Process the data returned from the API call

	# Create an empty list which will be used to contain data for all valid games for the contest date.
	gamelist = []
	# Use error_found and warning_count to keep track of errors/warnings found during data validation.
	error_found = False
	warning_count = 0
	# Use game_count to keep track of the number of games to be loaded for the upcoming contest
	game_count = 0

	# Loop through the game data returned by the API call.  It's in the form of a list of dictionaries, with a
	# separate dictionary for each game.
	for game in odds_data:
		# Use game_error-found and game_warning_found if an error or warning is found for a particular game.
		game_error_found = False
		game_warning_found = False
		# Process the date and time when the game is scheduled to begin.  In the API data, they are represented
		# as a string in UTC-Z format (<date>T<time>Z). The Python datetime module doesn't handle this type of
		# format directly, so some manipulation is required to change the "Z" to "+00:00"
		game_datetime_UTC = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
		# Convert the UTC date/time to Eastern time.  All times in Beat the Odds are in Eastern time.
		game_datetime_ET = game_datetime_UTC.astimezone(ZoneInfo("America/New_York"))
		# Separate the date/time into two variables, one for date and one for time.
		game_date = game_datetime_ET.date()
		game_time = game_datetime_ET.time()

		# If the game date is not equal to the contest date, skip this game and proceed to the next.
		if game_date != compare_date:
			continue

		# Get the name of the visiting team from the API data
		name_away = game['away_team']
		# Use the name to access the Team record in the Beat the Odds database.
		try:
			team = Team.objects.get(name=name_away)
		except:
			error_found = True
			game_error_found = True
			message = "No match found for team name " + name_away
			logger.error(message)
		else:
			# Set team_away to the 2 or 3-letter abbreviation for the team.  The team abbreviation is stored 
			# in the Game record in the database, rather than the full team name.
			team_away = team.abbrev
		# Do the same for the home team.
		name_home = game['home_team']
		try:
			team = Team.objects.get(name=name_home)
		except:
			error_found = True
			game_error_found = True
			message = "No match found for team name " + name_home
			logger.error(message)
		else:
			team_home = team.abbrev

		# Use the "outcomes" key in the API data to get the moneyline odds for the away and home teams.
		# Note: The "outcomes" key for the home team is generally listed first, followed by the visiting team.
		# But sometimes (not sure why) the order is reversed.  Hence, the if/else logic below.
		if game['bookmakers']:
			if game['bookmakers'][0]['markets'][0]['outcomes'][0]['name'] == name_away:
				odds_away = game['bookmakers'][0]['markets'][0]['outcomes'][0]['price']
				odds_home = game['bookmakers'][0]['markets'][0]['outcomes'][1]['price']
			else:
				odds_away = game['bookmakers'][0]['markets'][0]['outcomes'][1]['price']
				odds_home = game['bookmakers'][0]['markets'][0]['outcomes'][0]['price']			
		else:
			odds_away = None
			odds_home = None

		# If the odds data for a particular game is missing, set the warning-found flag and post a message
		# to the console.
		if odds_away == None or odds_home == None:
			game_warning_found = True
			warning_count += 1
			message = "Odds not yet posted for " + team_away + " vs " + team_home
			logger.warning(message)

		# If an error or warning was dound during validation, skip this game and proceed to the next.
		if game_error_found == True or game_warning_found == True:
			continue

		# Increment game_count
		game_count += 1
		# Create an empty dictionary which will be used to contain data for a specific game.
		gamedict = {}
		# Load the dictionary with data that will be used to populate a Game record in the database.
		gamedict['game_date'] = game_date
		gamedict['game_time'] = game_time
		gamedict['team_away'] = team_away
		gamedict['team_home'] = team_home
		gamedict['odds_away'] = odds_away
		gamedict['odds_home'] = odds_home
		# Add this game to the "gamelist" list.
		gamelist.append(gamedict)

	# If less than 10 valid games were found, log an error message and set error_found to True.
	# if game_count < 10:
	# 	error_found = True
	# 	message = "Need 10 or more games. " + str(game_count) + " were found."
	# 	logger.error(message)

	# Check if a Contest record already exists for the upcoming period (tomorrow for MLB, 
	# the upcoming weekend for NFL).  If so, log an error message and set error_found to True.
	league = "MLB"
	# The "season" format is a 4-digit year
	season = compare_date.strftime("%Y")
	# The "period" format is "mmm d" for MLB, "Week n" for NFL 
	period = compare_date.strftime("%b %-d")
	contest = Contest.objects.filter(league=league, season=season, period=period)
	if len(contest) > 0:
		error_found = True
		message = "A contest record already exists for " + league + "-" + season + "-" + period
		logger.error(message)

	# If any errors were found during validation, log an error message and terminate the process.
	if error_found == True:
		message = "Errors found - MLB odds process failed to complete"
		logger.error(message)
	else:
	# If odds were missing for any games and the time deadline has been reached, log a warning message
	# and terminate the process.
		if warning_count > 0 and current_time < deadline:
			message = "Warning - Odds missing for " + str(warning_count) + " game(s)."
			logger.warning(message)
			message = "MLB odds process not completed"
			logger.warning(message)
		else:
			# If an active Contest record exists, change its status field to "Closed" 
			contests = Contest.objects.filter(league=league, status="Active")
			for c in contests:
				c.status="Closed"
				c.save()

			# Create a new Contest record for the upcoming contest.
			c = Contest(league= league, season=season, period=period, num_picks=5, status="Active")
			c.save()

			# For each game in gamelist, create a new Game record, associate it with the Contest record (via the
			# foreigb key field), and populate it with the game date, game time, team names, and Moneyline odds. 
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

			# Log a message that the process has completed successfully.
			logger.info("MLB odds process completed successfully for " + str(game_count) + " games.")



###  LOAD_MLB_SCORES  ###



def load_mlb_scores():
	# Issue an API call to get the latest scores in JSON format
	SPORT = "baseball_mlb"
	API_KEY = "f13fe3a3f1ea67d9a1c15d549efc719e"
	url = 'https://api.the-odds-api.com/v4/sports/' + SPORT + '/scores/?apiKey=' + API_KEY + '&daysFrom=1'
	r = requests.get(url)
	odds_data = r.json()

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
	for game in odds_data:
		game_error_found = False

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
			gme_error_found = True
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

	# Get the Contest record for the recently completed contest (yesterdayfor MLB, 
	# the prior weekend for NFL).  If no Contest record found, log an error message
	# and terminate the process.
	league = "MLB"
	season = compare_date.strftime("%Y")
	period = compare_date.strftime("%b %-d")
	try:
		contest = Contest.objects.get(league=league, season=season, period=period)
	except:
		error_found = True
		message = "Contest record not found for " + league + "-" + season + "-" + period
		logger.error(message)

	if error_found == True:
		message = "MLB scores process failed to complete"
		logger.warning(message)
	else:
		# For each game in gamelist, update the corresonding Game record, populating it with the scores
		# and outcomes. 
		for game in gamelist:
			team_away = game['team_away']
			team_home = game['team_home']
			score_away = game['score_away']
			score_home = game['score_home']
			outcome_away = game['outcome_away']
			outcome_home = game['outcome_home']
			try:
				g = Game.objects.get(contest=contest, team_away=team_away, team_home=team_home)
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

		# Tally up the points, wins, losses, and ties for each participant, and
		# update their result record accordingly.
		results = Result.objects.filter(contest=contest)
		if len(results) == 0:
			message = "There were no picks for the " + period + " contest."
			logger.warning (message)
			logger.info("MLB scores process completed successfully")
		else:
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
			# Determine the winner of the contest and update the winner field in the Contest record.
			results = Result.objects.filter(contest=contest).order_by("-points")
			contest.winner = results[0].participant.username
			# Change the status of the contest to "Complete", and send a 
			# messsage indicating success.
			contest.status = "Complete"
			contest.save()

			logger.info("MLB scores process completed successfully")



###  DELETE_OLD_JOB_EXECUTIONS  ###



# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way. 
# @util.close_old_connections
def delete_old_job_executions(max_age=604_800):
  """
  This job deletes APScheduler job execution entries older than `max_age` from the database.
  It helps to prevent the database from filling up with old historical records that are no
  longer useful.
  
  :param max_age: The maximum length of time to retain historical job execution records.
                  Defaults to 7 days.
  """
  DjangoJobExecution.objects.delete_old_job_executions(max_age)

