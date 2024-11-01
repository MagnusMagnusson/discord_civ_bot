from tkinter import CASCADE
from django.db import models
from django.utils import timezone

class Player(models.Model):
    name = models.CharField(max_length=60, null=False)
    id = models.CharField(max_length=256, null=False, primary_key=True)

class Game(models.Model):
    name = models.CharField(max_length = 60, null=False)
    id = models.BigAutoField(primary_key=True)
    guild = models.BigIntegerField()

class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    
    def mu(self):
        last_match = Match.objects.filter(matchplayer__gameplayer=self, finished=True).latest("date_finished")
        if(last_match == None):
            return 25.00
        else:
            return last_match.mu

    def sigma(self):
        last_match = Match.objects.filter(matchplayer__gameplayer=self, finished=True).latest("date_finished")
        if(last_match == None):
            return 25.00
        else:
            return last_match.sigma

class MatchPlayer(models.Model):
    gameplayer = models.ForeignKey(to=GamePlayer, on_delete=models.CASCADE)
    match = models.ForeignKey(to="Match", on_delete=models.CASCADE)
    rank = models.IntegerField()
    mu = models.FloatField()
    sigma = models.FloatField()

class Match(models.Model):
    id = models.BigAutoField(primary_key=True)
    game = models.ForeignKey(to = Game, null = False, on_delete=models.CASCADE)
    date_started = models.DateTimeField(default=timezone.now, null=False)
    date_finished = models.DateTimeField(null=True)
    players = models.ManyToManyField(to = GamePlayer, through=MatchPlayer)
    finished = models.BooleanField(default = False)

    def finish(self):
        if(self.finished):
            return
        else:
            self.finished = True
            self.date_finished = timezone.now()
            

