from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from datetime import datetime

from django_apscheduler import util

from .scripts import load_mlb_odds, load_mlb_scores, delete_old_job_executions

from django.conf import settings

import logging
logger = logging.getLogger("faganweb scripts")

def start():
	scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
	scheduler.add_jobstore(DjangoJobStore(), "default")

	scheduler.add_job(
	  load_mlb_odds,
	  trigger=CronTrigger(hour="20-22", minute=10),  
	  id="load_mlb_odds",  # The `id` assigned to each job MUST be unique
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added job 'load_mlb_odds'.")

	scheduler.add_job(
	  load_mlb_scores,
	  trigger=CronTrigger(hour="3-4", minute=10),  
	  id="load_mlb_scores",  # The `id` assigned to each job MUST be unique
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added job 'load_mlb_scores'.")

	scheduler.add_job(
	  delete_old_job_executions,
	  trigger=CronTrigger(
	    day_of_week="mon", hour="00", minute="00"
	  ),  # Midnight on Monday, before start of the next work week.
	  id="delete_old_job_executions",
	  max_instances=1,
	  replace_existing=True,
	)
	logger.info("Added weekly job: 'delete_old_job_executions'.")

	scheduler.start()
