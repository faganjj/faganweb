from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import Http404
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum

from .models import Contest, Team, Game, Result, Pick, User


def index(request):
	""" The home page for Beat the Odds """

	# Get the most recent Contest record.  (Sort contest records by
	# contest.id.  Note:  The "-" indicates descending order.  The [0]
	# indicates the first record in the resulting queryset, which will
	# be the most recent).

	request.session['app'] = "beat_the_odds:index"
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

	# Check if the "Make Picks" button has been clicked.  If not, render 
	# the index.html template.
	if request.method == 'POST':

		if not request.user.is_authenticated:
			messages.warning(request, 'You must be logged in to continue.  Click "Log in" in the navigation bar above.')
			messages.warning(request, 'If you do not already have a FaganWeb account, click "Register" instead.')
			return redirect('beat_the_odds:index')

		league = request.POST.get('league')

	# Check if there is an active contest for the selected league.
	# If not, issue a warning message and re-direct to the index view. 
		try:
			contest = Contest.objects.get(league=league, status='Active') 
		except:
			message = "No active " + league + " contest"
			messages.warning(request, message)
			return redirect('beat_the_odds:index')

		user = request.user
		# Get today's date.  It will be compared to each game date, to determine
		# if the gsme can be legitimately picked.
		compare_date = date.today()
		compare_time = datetime.now().time()
		# But if the contest record has been created for test purposes, set the 
		# compare date to an arbitrary date in the past.
		if contest.test_contest:
			compare_date = date(2000,1,1)
		# Get all of the game records for the active contest ("game_set" uses
		# one-to-many relationship to get the game records).
		games = contest.game_set.all().order_by('game_date', 'game_time')
		mypicks = []
		oldpicks = []

		# Check if the Submit button has been clicked.  If so, validate and
		# save the picks.  If not, get the user's prior picks (if there are any)
		# in case they want to change them.
		if request.method == 'POST' and 'submitpicks' in request.POST:
			mypicks = request.POST.getlist('picks')
			# Initialize 'valid' to True prior to validation.
			valid = True
			# Make sure the user has made the correct number of picks.
			if len(mypicks) != contest.num_picks:
				valid=False
				message = "You need to pick " + str(contest.num_picks) + " winners. You picked " + str(len(mypicks)) +". Please try again." 
				messages.error(request, message)
			for game in games:
				# Make sure the user has not picked 2 winners for the same game.
				compare_away = game.team_away + "," + game.game_time.strftime("%H:%M")
				compare_home = game.team_home + "," + game.game_time.strftime("%H:%M")
				if compare_away in mypicks and compare_home in mypicks:
					valid=False
					messages.error(request, "You picked 2 winners for the same game. Please try again.")
				# Also make sure the user has not made a pick for a game that has already started.
				picks = Pick.objects.filter(contest=contest, participant=user)
				for pick in picks:
					compare_pick = pick.abbrev + "," + pick.game_time.strftime("%H:%M")
					oldpicks.append(compare_pick)
				if ((compare_away in mypicks and compare_away not in oldpicks) or (compare_home in mypicks and compare_home not in oldpicks)) \
				and (compare_date > game.game_date or (compare_date == game.game_date and compare_time > game.game_time)):
					valid=False
					messages.error(request, "You made a pick for a game that already started.")
			# If picks are valid, delete any prior picks and save the new picks.
			# Also, create an initialized Result record for the user.  It serves as a
			# junction record between Contest and User.
			if valid == True:
				Pick.objects.filter(contest=contest, participant=user).delete()
				for pick in mypicks:
					abbrev, game_time = pick.split(",")
					try:
						g = Game.objects.get(contest=contest, team_away=abbrev, game_time=game_time)
					except:
						g = Game.objects.get(contest=contest, team_home=abbrev, game_time=game_time)
					p = Pick(contest=contest, participant=request.user, abbrev=abbrev, game_time=game_time, game_id=g.game_id)
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
				compare_pick = pick.abbrev + "," + pick.game_time.strftime("%H:%M")
				mypicks.append(compare_pick)

		# Build a form listing all of the games info along with checkboxes for
		# picking winners. If prior picks have been made by this user, the 
		# picked-away and picked-home fields will be used to instruct the template
		# where to put checkmarks.
		season = contest.season
		period = contest.period
		num_picks = contest.num_picks
		for game in games:
			if compare_date < game.game_date or (compare_date == game.game_date and compare_time < game.game_time):
				game.eligible = True
			else:
				game.eligible = False
			abbrev_away = game.team_away
			compare_away = abbrev_away + "," + game.game_time.strftime("%H:%M")
			if len(mypicks) > 0:
				if compare_away in mypicks:
					game.picked_away = True
			team_away = Team.objects.get(league=league, abbrev=abbrev_away)
			game.name_away = team_away.name
			abbrev_home = game.team_home
			compare_home = abbrev_home + "," + game.game_time.strftime("%H:%M")
			if len(mypicks) > 0:
				if compare_home in mypicks:
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

	return render(request, 'beat_the_odds/index.html', context)


# If the user is not logged-in, redirect to the login page.

@login_required
def makepicks(request, league):
	""" Create a form for picking winners of games """

	# Check if there is an active contest for the selected league.
	# If so, redirect to the index view.  If not, issue a 
	# warning message and re-render index.html
	try:
		Contest.objects.get(league=league, status='Active') 
	except:
		message = "No active " + league + " contest"
		messages.warning(request, message)
		return redirect('beat_the_odds:index')

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
		# Make sure the user has made the correct number of picks.
		if len(mypicks) != contest.num_picks:
			valid=False
			message = "You need to pick " + str(contest.num_picks) + " winners. You picked " + str(len(mypicks)) +". Please try again." 
			messages.error(request, message)
		# Make sure the user has not picked 2 winners for the same game.
		for game in games:
			compare_away = game.team_away + "," + game.game_time.strftime("%H:%M")
			compare_home = game.team_home + "," + game.game_time.strftime("%H:%M")
			# compare_home = game.team_home + "," + str(game.game_time)
			if compare_away in mypicks and compare_home in mypicks:
				valid=False
				messages.error(request, "You picked 2 winners for the same game. Please try again.")
		# If picks are valid, delete any prior picks and save the new picks.
		# Also, create an initialized Result record for the user.  It serves as a
		# junction record between Contest and User.
		if valid == True:
			Pick.objects.filter(contest=contest, participant=user).delete()
			for pick in mypicks:
				abbrev, game_time = pick.split(",")
				p = Pick(contest=contest, participant=request.user, abbrev=abbrev, game_time=game_time)
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
			compare_pick = pick.abbrev + "," + pick.game_time.strftime("%H:%M")
			mypicks.append(compare_pick)

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
		compare_away = abbrev_away + "," + game.game_time.strftime("%H:%M")
		if len(mypicks) > 0:
			if compare_away in mypicks:
				game.picked_away = True
		team_away = Team.objects.get(league=league, abbrev=abbrev_away)
		game.name_away = team_away.name
		abbrev_home = game.team_home
		compare_home = abbrev_home + "," + game.game_time.strftime("%H:%M")
		if len(mypicks) > 0:
			if compare_home in mypicks:
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
		scope = request.POST.get('scope')

		# make sure there's at least one record with status of "Complete" for the 
		# selected league.
		try:
			contest = Contest.objects.filter(league=league, status='Complete').order_by('-id')[0]
		except:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			context = {'league': league, 'scope': scope}
			return render(request, 'beat_the_odds/ranking.html', context)
		season = contest.season
		user = request.user
		# Get all of the result records for the user for completed contests for the current league and season
		results = Result.objects.filter(participant=user, contest__league=league, contest__season=season, contest__status='Complete').order_by('-id')
		if len(results) == 0:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			context = {'league': league, 'scope': scope}
			return render(request, 'beat_the_odds/results.html', context)
		# Process the user's results records
		result_count = 0
		gamelist = []
		for result in results:
			# if result.contest.status == "Active":
			# 	if scope == "latest":
			# 		message = "No " + league + " results yet for " + result.contest.period
			# 		messages.warning(request, message)
			# 		context = {'league': league, 'scope': scope}
			# 		return render(request, 'beat_the_odds/results.html', context)	
			# 	else:	
			# 		continue
			# if result.contest.status == "Complete":
			result_count +=1
			if scope == "latest" and result_count > 1:
				break
			period = result.contest.period
			# Get all of the user's picks for the contest associated with this result record.
			picks = Pick.objects.filter(contest=result.contest, participant=user)
			mypicks = []
			for pick in picks:
				mypicks.append(pick.abbrev)
			# Get all of the game records for the contest associated with this result record.
			games = result.contest.game_set.all()
			mytotal = 0
			pick_count = 0
			# All of the game redords will be passed to the template, but the 
			# template will only display the games with picked_away or 
			# picked_home = True

			for game in games:
				for pick in picks:
					if (game.team_away == pick.abbrev and game.game_id == pick.game_id) \
					or (game.team_home == pick.abbrev and game.game_id == pick.game_id):
						pick_count += 1
						game.period = period
						game.picknum = pick_count
						game.num_picks = result.contest.num_picks
						game.status = result.contest.status
						team_away = Team.objects.get(league=league, abbrev=game.team_away)
						game.name_away = team_away.name
						team_home = Team.objects.get(league=league, abbrev=game.team_home)
						game.name_home = team_home.name
						if game.team_away == pick.abbrev and game.game_id == pick.game_id:
							game.picked_away = True
							if game.status == "Complete":
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
								game.mytotal = mytotal 
						if game.team_home == pick.abbrev and game.game_id == pick.game_id:
							game.picked_home = True
							if game.status == "Complete":
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
								game.mytotal = mytotal
						gamelist.append(game)
		context = {'league': league, 'season': season, 'period': period, 'scope': scope, 'games': gamelist}
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
			context = {'league': league, 'scope': scope}
			return render(request, 'beat_the_odds/ranking.html', context)
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
			position = 0
			for result in results:
				# Exclude users who do not have any results yet
				participant = User.objects.get(id=result['participant'])
				result['participant'] = participant
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

