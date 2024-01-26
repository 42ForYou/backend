from django.contrib import admin
from .models import Game, GameRoom, GamePlayer, SubGame


admin.site.register(Game)
admin.site.register(GameRoom)
admin.site.register(GamePlayer)
