
import warnings

# Ignore dateparser warnings regarding pytz
warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from datetime import datetime

from django_apscheduler import util

from .scripts import load_mlb_odds, load_mlb_scores, load_nfl_odds, load_nfl_scores, delete_old_job_executions

from django.conf import settings

import logging
logger = logging.getLogger("faganweb scripts")

def start():

	scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
	scheduler.add_jobstore(DjangoJobStore(), "default")

	# scheduler.add_job(
	#   load_mlb_odds,
	#   trigger=CronTrigger(hour="20-22", minute=0),  
	#   id="load_mlb_odds",  # The `id` assigned to each job MUST be unique
	#   max_instances=1,
	#   replace_existing=True,
	# )
	# logger.info("Added job 'load_mlb_odds'.")

	# scheduler.add_job(
	#   load_mlb_scores,
	#   trigger=CronTrigger(hour="5-6", minute=0),  
	#   id="load_mlb_scores",  # The `id` assigned to each job MUST be unique
	#   max_instances=1,
	#   replace_existing=True,
	# )
	# logger.info("Added job 'load_mlb_scores'.")

	scheduler.add_job(
	  load_nfl_odds,
	  trigger=CronTrigger(day_of_week="tue", hour=12, minute=0),  
	  id="load_nfl_odds",  # The `id` assigned to each job MUST be unique
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added job 'load_nfl_odds'.")

	scheduler.add_job(
	  load_nfl_scores,
	  trigger=CronTrigger(day_of_week="fri,sat,sun,mon,tue", hour=3, minute=0),  
	  id="load_nfl_scores",  # The `id` assigned to each job MUST be unique
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added job 'load_nfl_scores'.")

	scheduler.add_job(
	  load_nfl_scores,
	  trigger=CronTrigger(day_of_week="sat,sun,mon", hour=20, minute=30),  
	  id="load_nfl_scores_2",  # The `id` assigned to each job MUST be unique
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added job 'load_nfl_scores'.")

	scheduler.add_job(
	  delete_old_job_executions,
	  trigger=CronTrigger(
	    day_of_week="mon", hour=0, minute=0
	  ),  # Midnight on Monday, before start of the next work week.
	  id="delete_old_job_executions",
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added weekly job: 'delete_old_job_executions'.")

	scheduler.start()
