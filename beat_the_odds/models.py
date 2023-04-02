
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

CONTEST_STATUS = [
	('Active', 'Active'),
	('Closed', 'Closed'),
	('Complete', 'Complete'),
]

LEAGUE_CHOICES = [
    ('NFL', 'NFL'),
    ('MLB', 'MLB'),
]

class Contest(models.Model):
	""" A set of games/events (an NFL week, an MLB day, etc) """
	league = models.CharField(max_length=10, choices=LEAGUE_CHOICES, default='NFL')
	season = models.CharField(max_length=10)
	period = models.CharField(max_length=10)
	num_picks = models.IntegerField()
	winner = models.CharField(max_length=20, blank=True)
	status = models.CharField(max_length=10, choices=CONTEST_STATUS, default='Active')
	test_contest = models.BooleanField(default=False)

	def __str__(self):
		""" Return a string representation of the model """
		return f"{self.league} - {self.season} - {self.period}"

class Team(models.Model):
	""" An NFL or MLB team """
	league = models.CharField(max_length=10, choices=LEAGUE_CHOICES, default='NFL')
	abbrev = models.CharField(max_length=3)
	name = models.CharField(max_length=30)

	def __str__(self):
		return f"{self.league}:  {self.abbrev} - {self.name}"
 
class Game(models.Model):
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	game_date = models.DateField()
	game_time = models.TimeField()
	team_away = models.CharField(max_length=3)
	team_home = models.CharField(max_length=3)
	odds_away = models.IntegerField()
	odds_home = models.IntegerField()
	score_away = models.IntegerField(null=True, blank=True)
	score_home = models.IntegerField(null=True, blank=True)
	outcome_away = models.CharField(max_length=1, blank=True)
	outcome_home = models.CharField(max_length=1, blank=True)

	def __str__(self):
		return f"{self.game_date}: {self.team_away} ({self.odds_away})  at  {self.team_home} ({self.odds_home})"

class Result(models.Model):
	participant = models.ForeignKey(User, on_delete=models.CASCADE)
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	wins = models.IntegerField()
	losses = models.IntegerField()
	ties = models.IntegerField()
	points = models.IntegerField()

	def __str__(self):
		return f"{self.participant.username}  ({self.contest.league} - {self.contest.season} - {self.contest.period})"	

	class Meta:
		permissions = (("tally_results", "Tally results"),)

class Pick(models.Model):
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	participant = models.ForeignKey(User, on_delete=models.CASCADE)
	abbrev = models.CharField(max_length=3)

	def __str__(self):
		return f"{self.contest.league} - {self.contest.season} - {self.contest.period} - {self.participant.username} - {self.abbrev}"
