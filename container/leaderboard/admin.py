from django.contrib import admin
from leaderboard.models import Player, Game, Match, GamePlayer


class PlayerAdmin(admin.ModelAdmin):
    pass
admin.site.register(Player, PlayerAdmin)

class GameAdmin(admin.ModelAdmin):
    pass
admin.site.register(Game, GameAdmin)

class MatchAdmin(admin.ModelAdmin):
    pass
admin.site.register(Match, MatchAdmin)

class GamePlayerAdmin(admin.ModelAdmin):
    pass
admin.site.register(GamePlayer, GamePlayerAdmin)
