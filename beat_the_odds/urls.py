""" Defines URL patterns for beat_the_odds """

from django.urls import path

from . import views

app_name = 'beat_the_odds'
urlpatterns = [
	# Home page
	path('', views.index, name='index'),
	# Page for picking game winners
	path('makepicks/<league>', views.makepicks, name='makepicks'),
	# Page for displaying results
	path('results/', views.results, name='results'),
	# Page for displaying rankings
	path('ranking/', views.ranking, name='ranking'),
	# Page for tallying the points at the end of a contest
	path('tally/', views.tally, name='tally'),
]