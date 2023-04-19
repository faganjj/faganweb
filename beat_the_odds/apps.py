from django.apps import AppConfig
from django.conf import settings


class BeatTheOddsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'beat_the_odds'

    def ready(self):
        if settings.SCHEDULER_DEFAULT:
            from scripts import scheduler
            scheduler.start()