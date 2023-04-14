import os
import django
import logging

""" This is a test for deploying a Django-enabled Python script as a DO serverless function """

# The following statements allow the django ORM to be used in script.  It accesses the settings.py file for faganweb.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faganweb.settings')
django.setup()

# The following statement allows messages to be logged to the console
logger = logging.getLogger("beat_the_odds.views")

# Import the Django ORM models (tables) needed for this script.
from beat_the_odds.models import Contest

# Try to access records in the Contest table
contests = Contest.objects.filter (league="MLB")
if len(contests) > 0:
	logger.warning("Django test successful")
else:
	logger.warning("Django test failed")