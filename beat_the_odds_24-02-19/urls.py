""" Defines URL patterns for beat_the_odds """

from django.urls import path

from . import views

app_name = 'beat_the_odds'
urlpatterns = [
	# Home page
	path('', views.index, name='index'),
	# Page for displaying results
	path('results/', views.results, name='results'),
	# Page for displaying rankings
	path('ranking/', views.ranking, name='ranking'),
]