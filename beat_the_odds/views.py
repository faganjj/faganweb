from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import Http404
from datetime import date
from django.db.models import Sum

from .models import Contest, Team, Game, Result, Pick, User
# from .forms import PicksForm

# Create your views here.

def index(request):
	""" The home page for Beat the Odds """

	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No contests.")
		return render(request,'beat_the_odds/index.html')
	league = contest.league
	context = {'league': league}

	if request.method == 'POST':
		league = request.POST.get('league')
		try:
			Contest.objects.get(league=league, status='Active') 
		except:
			message = "No active " + league + " contest"
			messages.warning(request, message)
		else:
			return redirect('beat_the_odds:makepicks', league)
	return render(request, 'beat_the_odds/index.html', context)


@login_required
def makepicks(request, league):
	""" Create a form for picking winners of games """

	contest = Contest.objects.get(league=league, status='Active')
	user = request.user
	games = contest.game_set.all()

	if request.method == 'POST':
		mypicks = request.POST.getlist('picks')
		valid = True
		if len(mypicks) != 5:
			valid=False
			message = "You need to pick " + str(contest.num_picks) + " winners. You picked " + str(len(mypicks)) +". Please try again." 
			messages.error(request, message)
		for game in games:
			if game.team_away in mypicks and game.team_home in mypicks:
				valid=False
				messages.error(request, "You picked 2 winners for the same game. Please try again.")
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
		mypicks = []
		for pick in picks:
			mypicks.append(pick.abbrev)

	season = contest.season
	period = contest.period
	num_picks = contest.num_picks
	compare_date = date.today()
	if contest.test_contest:
		compare_date = date(2000, 1, 1)
	for game in games:
		abbrev_away = game.team_away
		if len(picks) > 0:
			if abbrev_away in mypicks:
				game.picked_away = True
		team_away = Team.objects.get(abbrev=abbrev_away)
		game.name_away = team_away.name
		abbrev_home = game.team_home
		if len(picks) > 0:
			if abbrev_home in mypicks:
				game.picked_home = True
		team_home = Team.objects.get(abbrev=abbrev_home)
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

	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No results yet")
		return redirect('beat_the_odds: index')	
	league = contest.league
	context = {'league': league}
	if request.method == 'POST':
		league = request.POST.get('league')
		try:
			contest = Contest.objects.filter(league=league, status='Complete').order_by('-id')[0]
		except:
			message = "No " + league + "No results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:results')
		user = request.user
		results = contest.game_set.all()
		season = contest.season
		period = contest.period
		picks = Pick.objects.filter(contest=contest, participant=user)
		if len(picks) == 0:
			message = "No " + league + " results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:results')
		games = contest.game_set.all()
		mypicks = []
		for pick in picks:
			mypicks.append(pick.abbrev)
		mytotal = 0
		for game in games:
			if game.team_away in mypicks or game.team_home in mypicks:
				team_away = Team.objects.get(abbrev=game.team_away)
				game.name_away = team_away.name
				team_home = Team.objects.get(abbrev=game.team_home)
				game.name_home = team_home.name
				if game.team_away in mypicks:
					game.picked_away = True
					if game.odds_away > 0:
						game.points_away = game.odds_away
					else:
						game.points_away = round(-100 / (game.odds_away/100))
					if game.outcome_away == "W":
						game.mypoints_away = game.points_away
					elif game.outcome_away == "L":
						game.mypoints_away = -100
					elif game.outcome_away == "T":
						game.mypoints_away = 0
					mytotal += game.mypoints_away
				if game.team_home in mypicks:
					game.picked_home = True
					if game.odds_home > 0:
						game.points_home = game.odds_home
					else:
						game.points_home = round(-100 / (game.odds_home/100))	
					if game.outcome_home == "W":
						game.mypoints_home = game.points_home
					elif game.outcome_home == "L":
						game.mypoints_home = -100
					elif game.outcome_home == "T":
						game.mypoints_home = 0
					mytotal += game.mypoints_home
		context = {'league': league, 'season': season, 'period': period, 'games': games, 'mytotal': mytotal}
	return render(request, 'beat_the_odds/results.html', context)


@login_required
def ranking(request):
	
	""" Display participant ranking for most recent period or season-to-date """

	try:
		contest = Contest.objects.order_by('-id')[0]
	except:
		messages.error(request, "No results yet")
		return redirect('beat_the_odds: index')	
	league = contest.league
	season = contest.season
	period = contest.period
	context = {'league': league}
	if request.method == 'POST':
		league = request.POST.get('league')
		scope = request.POST.get('scope')
		try:
			contest = Contest.objects.filter(league=league, status='Complete').order_by('-id')[0]
		except:
			message = "No " + league + "No results yet"
			messages.warning(request, message)
			return redirect('beat_the_odds:results')
		if scope == "contest":
			results = Result.objects.filter(contest=contest).order_by('-points')
			position = 0
			for result in results:
				position += 1
				if position == 1 and result.participant == request.user:
					messages.success(request, "Congratulations.  You are #1!!")
				else:
					if result.participant == request.user:
						message = "You are ranked #" + str(position) + " of " + str(len(results)) + " participants."
						messages.info(request, message)
		else:
			results = Result.objects.filter(contest__season=season).order_by('participant')
			results = results.values('participant').order_by('participant') \
				.annotate(points=Sum('points'), wins=Sum('wins'), losses=Sum('losses'), ties=Sum('ties')).order_by('-points')
			for result in results:
				participant = User.objects.get(id=result['participant'])
				result['participant'] = participant
			position = 0
			for result in results:
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
@permission_required('beat_the_odds.tally_results', raise_exception=True)
def tally(request):
	""" Create a form to tally the results of a contest """

	contests = Contest.objects.filter(status='Active')

	if request.method == 'POST' and len(contests) > 0:
		contest = request.POST.get('contest')
		contest = Contest.objects.get(id=contest)
		results = Result.objects.filter(contest=contest)
		for result in results:
			participant = result.participant
			picks = Pick.objects.filter(contest=contest, participant=participant)
			mypicks = []
			for pick in picks:
				mypicks.append(pick.abbrev)
			wins = losses = ties = points = 0
			games = contest.game_set.all()
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
		contest.status = "Complete"
		contest.save()
		messages.success(request, "Results tallied.  Contest closed")

	context = {'contests': contests}
	return render(request, 'beat_the_odds/tally.html', context)