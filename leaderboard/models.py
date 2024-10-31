from tkinter import CASCADE
from django.db import models
from django.utils import timezone

class Player(models.Model):
    name = models.CharField(max_length=60, null=False)
    id = models.CharField(max_length=256, null=False, primary_key=True)

class Game(models.Model):
    name = models.CharField(max_length = 60, null=False)
    id = models.BigAutoField(primary_key=True)

class Match(models.Model):
    id = models.BigAutoField(primary_key=True)
    game = models.ForeignKey(to = Game, null = False, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now, null=False)
    players = models.ManyToManyField(to = Player)

class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    ranking = models.IntegerField(default=25)