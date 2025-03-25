from datetime import datetime
from leaderboard.models import Game, GamePlayer, Match, MatchPlayer, Player
from asgiref.sync import sync_to_async
import math

@sync_to_async
def createLeague(name, guild):
    leagues = len(Game.objects.filter(guild = guild.id))
    if(leagues >= 100):
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
        message = "# "+name+ " rankings ("+str(1+page)+"/"+str(math.ceil(len(players)/25))+")\n"
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
        players = sorted(players, key=lambda t: t.sigma)
        players = sorted(players, key=lambda t: -t.mu)

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

@sync_to_async
def recalculateMatch(match_id, name, guild):
    league = Game.objects.filter(guild = guild.id, name = name)
    if(len(league) == 0):
        return [False, "League "+name+" does not exist."]
    return [True, league[0].recalculate(match_id)]
   

@sync_to_async
def  registerMatch(guild, name, members):
    league = Game.objects.filter(guild = guild.id, name = name)
    if(len(league) == 0):
        return [False, "League "+name+" does not exist"]
    gamePlayers = []
    for m in members:
        p = Player.objects.filter(id = m.id)
        if(len(p) == 0):
            return [False, m.name + " has not joined this league. Have them join first"]
        gp = GamePlayer.objects.filter(player = p[0], game = league[0])
        if(len(gp) == 0):            
            return [False, m.name + " has not joined this league. Have them join first"]
        gamePlayers.append(gp[0])
    match = Match()
    match.date_started = datetime.now()
    match.game = league[0]
    match.save()
    i = 0
    for gp in gamePlayers:
        mp = MatchPlayer()
        mp.match = match
        mp.gameplayer = gp
        mp.rank = i
        mp.save()
        i += 1
    i = 1
    message = "The following match is being reported in "+name+"\nThe results were reported as follows:"
    message += "\n"
    for m in members:
        message += str(i) + ". " + m.mention + "\n"

    message += "If the results are correct, would a majority of the members mentioned confirm by reacting to this message \n"
    message += "The report will be invalidated if not confirmed in 72 hours, and this message will be deleted."
    return [True, message, match]

@sync_to_async
def validate_match_payload(payload, reaction_users):
    message = payload.message_id
    print(message)
    match = Match.objects.filter(finished = False, message_id = message)
    print(match)
    if(len(match) == 1):
        match = match[0]
        matchPlayers = match.matchplayer_set.all()
        players = [str(x.gameplayer.player.id) for x in matchPlayers]
        needed_votes = math.ceil((len(players) + 0.5) / 2)
        print("Need " + str(needed_votes) + " votes")
        print(players)
        print(payload.member.id)
        if(str(payload.member.id) in players):
            print("Players was a member of match")
            print("Need " + str(needed_votes) + " votes")
            valid_votes = [x for x in players if x in reaction_users]
            if(len(valid_votes) >= needed_votes):
                return True
    return False

@sync_to_async
def finish_match(match):
    if(match.finished):
        return
    else:
        league = match.game.name
        match.finish()
        results = match.results()
        m = "# "+league + " MATCH OVER\n"
        m += " ===================== \n"
        for player in results :
            print(player.changeMu())
            sign = "+" if player.changeMu() >= 0 else ""
            m += str(player.rank + 1) + ". " + player.gameplayer.player.name + ". New ranking:  "'{0:.2f}'.format(player.gameplayer.mu) + " (" + sign + '{0:.2f}'.format(player.changeMu()) + ") \n"
        m += "\n===================== \n"
        return m

@sync_to_async
def getMatchFromMessage(message_id):
    match = Match.objects.filter(message_id = message_id)
    return match[0]

@sync_to_async
def listMatches(guild, league_name):
    league = Game.objects.filter(guild = guild.id, name = league_name)
    if not league:
        return [True, "The league " + league_name + " does not exist"] 
    else:
        league = league[0]
    matches = Match.objects.filter(game = league)
    if(len(matches) == 0):
        return [True, "No matches have been played under the league " + league.name]
    else:
        string = "The following matches exist for league " + league.name +"\n"
        for match in matches:
            string = string + "ID: " + str(match.id) + ": " + str(match.date_started) + " to " + str(match.date_finished) + "\n"
        return [True, string]

        