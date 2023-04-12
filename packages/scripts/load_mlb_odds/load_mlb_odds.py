import os
import django
import logging
import requests
import json
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

def main():

	# The following statement allows messages to be logged to the console
	# Here's a link to an article that provides more info:
	# https://medium.com/@torkashvand/a-comprehensive-guide-to-logging-in-django-e041f311bcb7
	logger = logging.getLogger("beat_the_odds.views")

	# The following statements allow the django ORM to be used in scripts.  It accesses the settings.py file for faganweb.
	# Here's a link to a video that explains it:
	# https://www.google.com/search?
	#	q=use+django+orm+in+python+script&rlz=1C5CHFA_enUS897US897&oq=use+django+orm+in+python+script
	#	&aqs=chrome..69i57j0i390i650l4j69i60.33598j1j7&sourceid=chrome&ie=UTF-8#fpstate=ive&vld=cid:0c8bffb5,vid:AS01VoC9l5w
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faganweb.settings')
	django.setup()

	# Import the Django ORM models (tables) needed for this script.

	from beat_the_odds.models import Team, Contest, Game

	# Issue an API call to get the latest odds in JSON format.  the-odds-api.com is being used as the data source.
	SPORT = "baseball_mlb"
	BOOKMAKER = "fanduel"
	API_KEY = "f13fe3a3f1ea67d9a1c15d549efc719e"
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
	# Use error_count and warning_count to keep track of errors/warnings found during data validation.
	error_count = 0
	warning_count = 0
	# Use game_count to keep track of the number of games to be loaded for the upcoming contest
	game_count = 0

	# Loop through the game data returned by the API call.  It's in the form of a list of dictionaries, with a
	# separate dictionary for each game.
	for game in odds_data:
		# Use error-found and warning_found if an error or warning is found for a particular game.
		error_found = False
		warning_found = False
		# Process the date and time when the game is scheduled to begin.  In the API data, they are represented
		# as a string in UTC-Z format (<date>T<time>Z). The Python datetime module doesn't handle this type of
		# format directly, so some manipulation is required to change the "Z" to "+00:00"
		game_datetime_UTC = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
		# Convert the UTC date/time to Easter time.  All times in Beat the Odds are in Eastern time.
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
			error_count += 1
			error_found = True
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
			error_count += 1
			error_found = True
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
			warning_found = True
			warning_count += 1
			message = "Odds not yet posted for " + team_away + " vs " + team_home
			logger.warning(message)

		# If an error or warning was dound during validation, skip this game and proceed to the next.
		if error_found == True or warning_found == True:
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

	# If less than 10 valid games were found, log an error message and increment error_count.
	if game_count < 10:
		error_count += 1
		message = "Need 10 or more games. " + str(game_count) + " were found."
		logger.error(message)

	# Check if a Contest record already exists for the upcoming period (tomorrow for MLB, 
	# the upcoming weekend for NFL).  If so, log an error message and increment error_count.
	league = "MLB"
	# The "season" format is a 4-digit year
	season = compare_date.strftime("%Y")
	# The "period" format is "mmm d" for MLB, "Week n" for NFL 
	period = compare_date.strftime("%b %-d")
	contest = Contest.objects.filter(league=league, season=season, period=period)
	if len(contest) > 0:
		error_count +=1
		message = "A contest record already exists for " + league + "-" + season + "-" + period
		logger.error(message)

	# If any errors were found during validation, log an error message and terminate the process.
	if error_count > 0:
		message = "Errors found - MLB odds process failed to complete"
		logger.error(message)
		exit()

	# If odds were missing for any games and the time deadline has been reached, log a warning message
	# and terminate the process.
	if warning_count > 0 and current_time < deadline:
		message = "Warning - Odds missing for " + str(warning_count) + " game(s)."
		logger.warning(message)
		message = "MLB odds process not completed"
		logger.warning(message)
		exit()

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
	logger.warning("MLB odds process completed successfully for" + str(game_count) + " games.")



