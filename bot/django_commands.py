from leaderboard.models import Game
from asgiref.sync import sync_to_async

@sync_to_async
def createLeague(name, guild):
    leagues = len(Game.objects.filter(guild = guild.id))
    if(leagues >= 1):
        return "Sorry, but each server can only create 100 leagues."
    elif(len(Game.objects.filter(guild = guild.id, name = name)) > 0):
        return "The league '"+name+"' already exists on this server"
    else:
        try:
            g = Game()
            g.guild = guild.id
            g.name = name
            g.save()
            return "The league '"+name+"' has been created for " + guild.name
        except Exception:
            return "Error executing command"

@sync_to_async
def listLeagues(guild):
    leagues = Game.objects.filter(guild = guild.id).order_by("name")
    message = guild.name + " has the following leagues:\n"
    if(len(leagues) == 0):
        return guild.name+ " has not created any leagues. An admin can create some with the command '!league create <name>'"
    else:
        for league in leagues:
            message += "* "+ league.name+" | Members:" + str(len(league.gameplayer_set.all())) + ", Matches: "+ str(len(league.match_set.all())) + "\n"
        print(message)
        return message
