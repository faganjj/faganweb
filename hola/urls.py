""" Defines URL patterns for appslist """

from django.urls import path

from . import views

app_name = 'hola'
urlpatterns = [
	# Home page
	path('', views.index, name='index'),
]