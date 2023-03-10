from django.db import models

# Create your models here.

class App(models.Model):
	""" An application being hosted on faganweb.com """
	title = models.CharField(max_length = 100)
	appname = models.CharField(max_length = 20)
	subdir = models.CharField(max_length = 20)
	text = models.TextField()
	active = models.BooleanField(default = False)

	def __str__(self):
		""" Return a short string representation of the app """
		return f"{self.text[:50]}..."