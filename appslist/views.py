from django.shortcuts import render

from .models import App

# Create your views here.

def index(request):
	""" Display all of the FaganWeb apps """
	request.session['app'] = "appslist:index"
	apps = App.objects.all().order_by('display_order')
	context = {'apps': apps}
	return render(request, 'appslist/index.html', context)