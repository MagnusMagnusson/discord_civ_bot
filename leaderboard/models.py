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

    def recalculate(self, fromMatchId):
            try:
                match = Match.objects.filter(id = fromMatchId)
                if match.count() == 1:  # Ensure we have exactly one match
                    invalid_players = set()
                    invalid_matches = set()
                    seen_matches = set()

                    # First match that triggered the invalidation process
                    initial_match = match.first()
                    invalid_matches.add(initial_match)
                    seen_matches.add(initial_match)

                    # First Pass: Identify all invalid matches
                    for current_match in list(invalid_matches):  # Convert set to list to allow iteration
                        # Add players from the current match to the invalid set
                        new_players = set(current_match.players.all()) - invalid_players
                        invalid_players.update(new_players)
                        current_match.finished = False

                        if new_players:
                            # Find future matches involving any newly invalid players
                            new_matches = Match.objects.filter(
                                game=current_match.game,
                                date_finished__gt=current_match.date_finished,
                                players__in=new_players
                            ).distinct()

                            # Add only unseen matches
                            for m in new_matches:
                                if m not in seen_matches:
                                    invalid_matches.add(m)
                                    seen_matches.add(m)
                                    m.finished = False

                    # --- Intermediate steps can be added here before recalculating matches ---
                    print(len(seen_matches))

                    # Second Pass: Recalculate all invalid matches
                    for match in sorted(invalid_matches, key=lambda m: m.date_finished or timezone.now()):
                        match.recalculate()

                    return "Recalculated " + str(len(seen_matches)) + " matches."
                else:
                    return "Math ID not found"
            except ex:
                print(ex)
                return "Failed to recalculate due to unexpected error. I hope the league isn't irrepairably ruined now"


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    
    @property    
    def mu(self):
        last_match = MatchPlayer.objects.filter(gameplayer=self, match__finished=True)
        if(len(last_match) == 0):
            print("NO MATCH; MEW")
            return DEFAULT_MU
        else:
            print("GET OLD; MEEE")
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

    @property
    def lastMu(self):
        now = timezone.now() if self.match.date_finished == None else self.match.date_finished
        last_match = Match.objects.filter(
            game=self.match.game,
            players=self.gameplayer,
            date_finished__lt=now, 
            finished = True
        ).order_by('-date_finished').first()  

        if last_match:
            last_match_player = MatchPlayer.objects.filter(
                match=last_match,
                gameplayer=self.gameplayer
            ).first() 

            if last_match_player and last_match_player.mu is not None:
                return last_match_player.mu  

        return DEFAULT_MU 

    @property
    def lastSigma(self):
        now = timezone.now() if self.match.date_finished == None else self.match.date_finished
        last_match = Match.objects.filter(
            game=self.match.game,
            players=self.gameplayer,
            date_finished__lt=now, 
        ).order_by('-date_finished').first()  

        if last_match:
            last_match_player = MatchPlayer.objects.filter(
                match=last_match,
                gameplayer=self.gameplayer
            ).first() 

            if last_match_player and last_match_player.mu is not None:
                return last_match_player.sigma 

        return DEFAULT_SIGMA
    
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
        if self.finished:
            return
        
        players = self.matchplayer_set.all()
        ratings = [(Rating(x.lastMu, x.lastSigma),) for x in players]
        rankings = [x.rank for x in players]
        
        new_rankings = rate(ratings, rankings)
        
        print("Old ratings")
        print(ratings)
        print(rankings)
        print("New ratings")
        print(new_rankings)
        
        # Update and commit player ratings
        for new_rank, player in zip(new_rankings, players):
            player.mu = new_rank[0].mu
            player.sigma = new_rank[0].sigma
            player.save()
            
        self.finished = True
        self.date_finished = timezone.now()
        self.save()
        
    def results(self):
        players = self.matchplayer_set.all().order_by("rank")
        return [x for x in players]     

    def recalculate(self):
        print("RECALCULATING MATCH " + str(self.id))   
        if self.finished:
            return
        
        players = self.matchplayer_set.all()
        ratings = [(Rating(x.lastMu, x.lastSigma),) for x in players]
        rankings = [x.rank for x in players]
        
        new_rankings = rate(ratings, rankings)
        
        print("Old ratings")
        print(ratings)
        print(rankings)
        print("New ratings")
        print(new_rankings)
        
        # Update and commit player ratings
        for new_rank, player in zip(new_rankings, players):
            player.mu = new_rank[0].mu
            player.sigma = new_rank[0].sigma
            player.save()
            
        self.finished = True
        self.save()