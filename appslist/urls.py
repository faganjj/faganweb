""" Defines URL patterns for appslist """

from django.urls import path

from . import views

app_name = 'appslist'
urlpatterns = [
	# Home page
	path('', views.index, name='index'),
]