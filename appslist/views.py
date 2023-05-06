from django.shortcuts import render

from .models import App

# Create your views here.

def index(request):
	""" Display all of the FaganWeb apps """
	apps = App.objects.all().order_by('id')
	context = {'apps': apps}
	return render(request, 'appslist/index.html', context)