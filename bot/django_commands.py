from leaderboard.models import Game, GamePlayer, Player
from asgiref.sync import sync_to_async
import math

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


async def printRanking(bot, guild, name, page):
    players = await getRanking(guild, name)
    if(players == None):
        return "The designated League '"+name+"' does not exist on this server"
    else:
        message = "# "+name+ " rankings ("+str(page)+"/"+str(math.ceil(len(players)/25))+")\n"
        message += "====================================== \n"
        message += "Rank | Name | Rating | Sigma | Matches\n"
        i =  page * 25
        for player in players[25*page : 25*(page + 1)]:
            i += 1
            member = await bot.fetch_user(player["id"])
            message +=str(i) + " | " + member.display_name + " | " + '{0:.2f}'.format(player["mu"]) + " | " + '{0:.2f}'.format(player["sigma"]) + "\n"
        message += "======================================"
        return message

@sync_to_async
def getRanking(guild, name):
    league = Game.objects.filter(guild = guild.id, name = name)
    if(len(league) == 0):
        return None
    else:
        league = league[0]
        players = league.gameplayer_set.all()
        players = sorted(players, key=lambda t: -t.sigma)
        players = sorted(players, key=lambda t: t.mu)

        return [{"id" : x.player_id, "sigma": x.sigma, "mu": x.mu} for x in players]

@sync_to_async
def addPlayerToLeague(member, name, guild):
    league = Game.objects.filter(guild = guild.id, name = name)
    if(len(league) == 0):
        return "League "+name+" does not exist, and so you cannot join it\nYou can list all leagues on the server with '!league list'"
    player = league[0].gameplayer_set.filter(player_id = member.id)
    if(len(player) == 1):
        return "You already belong to this league"
    else:
        try:
            p = Player.objects.filter(id = member.id)
            if(len(p) == 0):
                p = Player()
                p.id = member.id
                p.name = member.name
                p.save()
            else: 
                p = p[0]
            gp = GamePlayer()
            gp.player = p
            gp.game = league[0]
            gp.save()
            league[0].gameplayer_set.add(gp)
        except Exception as e:
            print(e)
            return "Unexpected error. Sorry!"
        else:
            return member.mention + " has joined the league " + name

