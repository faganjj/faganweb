from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

# Create your views here.

def register(request):
	""" Register a new user """
	if request.method != 'POST':
		nextpage = request.GET.get('next')
		# Display blank registration form
		form = UserCreationForm()
	else:
		# Process completed form
		nextpage = request.POST.get('next')
		form = UserCreationForm(data=request.POST)
		if form.is_valid():
			new_user = form.save()
			# Log the user in and then redirect to the home page
			login(request, new_user)
			if 'app' in request.session:
				nextpage = request.session['app']
			else:
				nextpage = 'appslist:index'
			return redirect(nextpage)
			# return redirect(request.POST.get('next'))

	# Display a blank or invalid form
	context = {'form': form, 'next': nextpage}
	return render(request, 'registration/register.html', context)