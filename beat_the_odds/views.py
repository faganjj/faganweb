from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import Http404
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum

from .models import Contest, Team, Game, Result, Pick, User
# from .forms import PicksForm

# The following statement allows messages to be logged to the console
# Here's a link to an article that provides more info:
# https://medium.com/@torkashvand/a-comprehensive-guide-to-logging-in-django-e041f311bcb7
# logger = logging.getLogger("beat_the_odds.views")

def index(request):
	""" The home page for Beat the Odds """

	# Get the most recent Contest record.  (Sort contest records by
	# contest.id.  Note:  The "-" indicates descending order.  The [0]
	# indicates the first record in the resulting queryset, which will
	# be the most recent).

	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No contests.")
		return render(request,'beat_the_odds/index.html')

	# Determine which league was specified in the most recent contest.
	# We'll pass it to the template, which will make that league the
	# default choice in the league dropdown list.
	league = contest.league
	context = {'league': league}

	# Check the Make Picks" button has been clicked.  If not, render 
	# the index.html template.
	if request.method == 'POST':
		league = request.POST.get('league')

	# Check if there is an active contest for the selected league.
	# If so, redirect to the makepicks page.  If not, issue a 
	# warning message and re-render index.html
		try:
			Contest.objects.get(league=league, status='Active') 
		except:
			message = "No active " + league + " contest"
			messages.warning(request, message)
		else:
			return redirect('beat_the_odds:makepicks', league)
	return render(request, 'beat_the_odds/index.html', context)


# If the user is not logged-in, redirect to the login page.
@login_required
def makepicks(request, league):
	""" Create a form for picking winners of games """

	# Get the active contest record for the specified league. There should
	# only be one.
	contest = Contest.objects.get(league=league, status='Active')
	
	user = request.user
	# Get all of the game records for the active contest ("game_set" uses
	# one-to-many relationship to get the game records).
	games = contest.game_set.all().order_by('game_date', 'game_time')
	mypicks = []

	# Check if the Submit button has been clicked.  If so, validate and
	# save the picks.  If not, get the user's prior picks (if there are any)
	# in case they want to change them.
	if request.method == 'POST':
		mypicks = request.POST.getlist('picks')
		# Initialize 'valid' to True prior to validation.
		valid = True
		# Make sure the user has made the correct 
		if len(mypicks) != contest.num_picks:
			valid=False
			message = "You need to pick " + str(contest.num_picks) + " winners. You picked " + str(len(mypicks)) +". Please try again." 
			messages.error(request, message)
		# Make sure the user has not picked 2 winners for the same game.
		for game in games:
			if game.team_away in mypicks and game.team_home in mypicks:
				valid=False
				messages.error(request, "You picked 2 winners for the same game. Please try again.")
		# If picks are valid, delete any prior picks and save the new picks.
		# Also, create an initialized Result record for the user.  It serves as a
		# junction record between Contest and User.
		if valid == True:
			Pick.objects.filter(contest=contest, participant=user).delete()
			for pick in mypicks:
				p = Pick(contest=contest, participant=request.user, abbrev=pick)
				p.save()
			try:
				Result.objects.get(participant=user, contest=contest)
			except:
				r = Result(participant=user, contest=contest, wins=0, losses=0, ties=0, points=0)
				r.save()
			messages.success(request, "Your picks have been submitted!")
			return redirect('beat_the_odds:index')
	else:
		picks = Pick.objects.filter(contest=contest, participant=user)
		for pick in picks:
			mypicks.append(pick.abbrev)

	# Build a form listing all of the games info along with checkboxes for
	# picking winners. If prior picks have been made by this user, the 
	# picked-away and picked-home fields will be used to instruct the template
	# where to put checkmarks.
	season = contest.season
	period = contest.period
	num_picks = contest.num_picks
	# Get today's date.  It will be compared to each game date, to determine
	# if the gsme can be legitimately picked.
	compare_date = date.today()
	compare_time = datetime.now().time()
	# But if the contest record has been created for test purposes, set the 
	# compare date to an arbitrary date in the past.
	if contest.test_contest:
		compare_date = date(2000,1,1)
	for game in games:
		if compare_date < game.game_date or (compare_date == game.game_date and compare_time < game.game_time):
			game.eligible = True
		else:
			game.eligible = False
		abbrev_away = game.team_away
		if len(mypicks) > 0:
			if abbrev_away in mypicks:
				game.picked_away = True
		team_away = Team.objects.get(league=league, abbrev=abbrev_away)
		game.name_away = team_away.name
		abbrev_home = game.team_home
		if len(mypicks) > 0:
			if abbrev_home in mypicks:
				game.picked_home = True
		team_home = Team.objects.get(league=league, abbrev=abbrev_home)
		game.name_home = team_home.name
		if game.odds_away > 0:
			game.points_away = game.odds_away
		else:
			game.points_away = round(-100 / (game.odds_away/100))
		if game.odds_home > 0:
			game.points_home = game.odds_home
		else:
			game.points_home = round(-100 / (game.odds_home/100))	

	context = {'league': league, 'season': season, 'period': period, 'num_picks': num_picks, \
		'games': games, 'compare_date': compare_date}
	return render(request, 'beat_the_odds/makepicks.html', context)


@login_required
def results(request):
	""" Display game results for the most recent period """

	# Get the most recent contest record, and determine which league was
	# specified. We'll pass it to the template, which will make that league the
	# default choice in the league dropdown list.
	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No results yet")
		return redirect('beat_the_odds:index')	
	league = contest.league
	context = {'league': league}
	# Check if the "Show Results" button has been clicked. If so, display
	# the most recent results.
	if request.method == 'POST':
		league = request.POST.get('league')
		# Get the most recent contest with a status of "Complete" for the
		# selected league.
		try:
			contest = Contest.objects.filter(league=league, status='Complete').order_by('-id')[0]
		except:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:results')
		user = request.user
		results = contest.game_set.all()
		season = contest.season
		period = contest.period
		# get all of the user's picks for the contest.
		picks = Pick.objects.filter(contest=contest, participant=user)
		if len(picks) == 0:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:results')
		# Get all of the game records for the mot recent completed contest
		games = contest.game_set.all()
		mypicks = []
		for pick in picks:
			mypicks.append(pick.abbrev)
		mytotal = 0
		# All of the game redords will be passed to the template, but the 
		# template will only display the games with picked_away or 
		# picked_home = True
		for game in games:
			if game.team_away in mypicks or game.team_home in mypicks:
				team_away = Team.objects.get(league=league, abbrev=game.team_away)
				game.name_away = team_away.name
				team_home = Team.objects.get(league=league, abbrev=game.team_home)
				game.name_home = team_home.name
				if game.team_away in mypicks:
					game.picked_away = True
					if game.odds_away > 0:
						game.points_away = game.odds_away
					else:
						game.points_away = round(-100 / (game.odds_away/100))
					if game.outcome_away == "W":
						game.mypoints = game.points_away
					elif game.outcome_away == "L":
						game.mypoints = -100
					elif game.outcome_away == "T":
						game.mypoints = 0
					mytotal += game.mypoints
				if game.team_home in mypicks:
					game.picked_home = True
					if game.odds_home > 0:
						game.points_home = game.odds_home
					else:
						game.points_home = round(-100 / (game.odds_home/100))	
					if game.outcome_home == "W":
						game.mypoints = game.points_home
					elif game.outcome_home == "L":
						game.mypoints = -100
					elif game.outcome_home == "T":
						game.mypoints = 0
					mytotal += game.mypoints
		context = {'league': league, 'season': season, 'period': period, 'games': games, 'mytotal': mytotal}
	return render(request, 'beat_the_odds/results.html', context)


@login_required
def ranking(request):
	
	""" Display participant ranking for most recent period or season-to-date """

	# Get the most recent contest record, and determine which league was
	# specified. We'll pass it to the template, which will make that league the
	# default choice in the league dropdown list.
	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No results yet")
		return redirect('beat_the_odds: index')	
	league = contest.league
	context = {'league': league}
	# Check if the "Show Ranking" button has been clicked. If so, display ranking.
	if request.method == 'POST':
		league = request.POST.get('league')
		scope = request.POST.get('scope')
		# make sure there's at least one record with status of "Complete" for the 
		# selected league.
		try:
			contest = Contest.objects.filter(league=league, status='Complete').order_by('-id')[0]
		except:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:ranking')
		season = contest.season
		period = contest.period
		# If "Latest Contest" was selected from the scope dropdown, display the ranking
		# for the latest contest. Otherwise, display ranking for season to-date.
		if scope == "contest":
			# Get result records for all users who participated in tne contest, sorted
			# by total points in descending order.
			results = Result.objects.filter(contest=contest).order_by('-points')
			position = 0
			for result in results:
				# For the user in position #1, display a congratulations message.
				# Otherise, display a message informing the user where they ranked
				# for this contest.
				position += 1
				if position == 1 and result.participant == request.user:
					messages.success(request, "Congratulations.  You are #1!!")
				else:
					if result.participant == request.user:
						message = "You are ranked #" + str(position) + " of " + str(len(results)) + " participants."
						messages.info(request, message)
		else:
			# Get result records for all users who participated in any contest for this 
			# league within the current season contest, sorted by total points in descending 
			# order.
			results = Result.objects.filter(contest__league=league, contest__season=season).order_by('participant')
			# Aggregate the points, wins, losses, and ties for the result records for each participant.
			# Sort by total points in descending order.  Note that this produces a dictionary rather
			# than a queryset, and needs to be proceesed differently (using square brackets notation).
			results = results.values('participant') \
				.annotate(points=Sum('points'), wins=Sum('wins'), losses=Sum('losses'), ties=Sum('ties')).order_by('-points')
			for result in results:
				participant = User.objects.get(id=result['participant'])
				result['participant'] = participant
			position = 0
			for result in results:
				# For the user in position #1, display a congratulations message.
				# Otherise, display a message informing the user where they ranked
				# for the season to-date.
				position += 1
				if position == 1 and result['participant'] == request.user:
					messages.success(request, "Congratulations.  You are #1!!")
				else:
					if result['participant'] == request.user:
						message = "You are ranked #" + str(position) + " of " + str(len(results)) + " participants."
						messages.info(request, message)
		context = {'league':league, 'season':season, 'period':period, 'scope':scope, 'results':results}
	return render(request, 'beat_the_odds/ranking.html', context)


@login_required
# Only authorized users can access this page. Otherise a 403 (Forbidden)
# exception will be raised.
@permission_required('beat_the_odds.tally_results', raise_exception=True)
def tally(request):
	""" Create a form to tally the results of a contest """

	# Get active contests.  There could be more than one (one for each league).
	contests = Contest.objects.filter(status='Active')

	# Check if "Tally" button has been clicked.
	if request.method == 'POST' and len(contests) > 0:
		# Check which contest has been selected.
		contest = request.POST.get('contest')
		# Get the contest record
		contest = Contest.objects.get(id=contest)
		# Get the initialized result record for each participant in the contest.
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
		messages.success(request, "Results tallied.  Contest closed")

	context = {'contests': contests}
	return render(request, 'beat_the_odds/tally.html', context)


def load_mlb_odds():

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
	logger.warning("MLB odds process completed successfully for " + str(game_count) + " games.")
