from django.contrib import admin

from matching.models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    pass
