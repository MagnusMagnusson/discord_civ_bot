from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from leaderboard.models import Game, Match

class MatchListView(View):
    template_name = 'matchlist.html'  # Set the template to render

    def get(self, request, game, *args, **kwargs):
        game = Game.objects.filter(id = game)
        if(len(game) == 0):
            return render(request, 'matchnotfound.html', context)


        # Query all Game objects from the database
        matches = Match.objects.filter(game = game[0]).order_by('date')
        
        # Define the context to pass to the template
        context = {
            'game': game[0],
            'matches': matches
        }
        
        # Render the template with the context and return the response
        return render(request, self.template_name, context)

class GameListView(View):
    template_name = 'gamelist.html'  # Set the template to render

    def get(self, request, *args, **kwargs):
        # Query all Game objects from the database
        games = Game.objects.all()
        
        # Define the context to pass to the template
        context = {
            'games': games
        }
        
        # Render the template with the context and return the response
        return render(request, self.template_name, context)