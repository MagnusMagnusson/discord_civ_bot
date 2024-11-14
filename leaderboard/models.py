from datetime import datetime
from tkinter import CASCADE
from django.db import models
from django.utils import timezone
from trueskill import Rating, rate

DEFAULT_MU = 25
DEFAULT_SIGMA = DEFAULT_MU / 3

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
    
    @property    
    def mu(self):
        last_match = MatchPlayer.objects.filter(gameplayer=self, match__finished=True)
        if(len(last_match) == 0):
            return DEFAULT_MU
        else:
            return last_match.latest("match__date_finished").mu

    @property
    def sigma(self):
        last_match = MatchPlayer.objects.filter(gameplayer=self, match__finished=True)
        if(len(last_match) == 0):
            return DEFAULT_SIGMA
        else:
            print("Here!")
            print(last_match)
            print(last_match.latest("match__date_finished"))
            print(last_match.latest("match__date_finished").mu)
            print(last_match.latest("match__date_finished").sigma)
            return last_match.latest("match__date_finished").sigma
    

class MatchPlayer(models.Model):
    gameplayer = models.ForeignKey(to=GamePlayer, on_delete=models.CASCADE)
    match = models.ForeignKey(to="Match", on_delete=models.CASCADE)
    rank = models.IntegerField(null=True)
    mu = models.FloatField(null=True)
    sigma = models.FloatField(null=True)    
    
    def changeMu(self):
        previous_match = MatchPlayer.objects.filter(gameplayer=self.gameplayer, match__finished=True).exclude(match = self.match)
        if(len(previous_match) == 0):
            return self.mu - DEFAULT_MU
        else:
            return self.mu - previous_match.latest("match__date_finished").mu

    def changeSigma(self):
        previous_match = MatchPlayer.objects.filter(gameplayer=self.gameplayer, match__finished=True).exclude(match = self.match)
        if(len(previous_match) == 0):
            return self.sigma - DEFAULT_SIGMA        
        else:
            return self.mu - previous_match.latest("match__date_finished").sigma

class Match(models.Model):
    id = models.BigAutoField(primary_key=True)
    game = models.ForeignKey(to = Game, null = False, on_delete=models.CASCADE)
    date_started = models.DateTimeField(default=timezone.now, null=False)
    date_finished = models.DateTimeField(null=True)
    players = models.ManyToManyField(to = GamePlayer, through=MatchPlayer)
    finished = models.BooleanField(default = False)
    message_id = models.CharField(null = True, max_length=256)

    def finish(self):
        if(self.finished):
            return
        else:
            players = self.matchplayer_set.all()
            ratings = [(Rating(x.mu, x.sigma),) for x in players]
            rankings = [x.rank for x in players]
            print(ratings)
            print(rankings)
            new_rankings = rate(ratings, rankings)
            i = 0
            print(new_rankings)
            for new_rank in new_rankings:
                player = players[i]
                player.mu = new_rank[0].mu
                player.sigma = new_rank[0].sigma
                player.save()
                i += 1
            self.finished = True
            self.date_finished = timezone.now()
            self.save()
    def results(self):
        players = self.matchplayer_set.all().order_by("rank")
        return [x for x in players]
            

