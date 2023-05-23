from django.contrib import admin

# Register your models here.

from .models import Contest, Team, Game, Result, Pick, OddsCount

admin.site.register(Contest)
admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Result)
admin.site.register(Pick)
admin.site.register(OddsCount)