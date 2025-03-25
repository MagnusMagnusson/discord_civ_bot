#coding:utf8
from audioop import add
from venv import create
import discord
from discord.ext import commands

from leaderboard.models import Match
from .django_commands import recalculateMatch, listMatches, registerMatch, createLeague, listLeagues, printRanking, addPlayerToLeague, validate_match_payload, getMatchFromMessage, finish_match
from asgiref.sync import sync_to_async
from .secret import BOT_AUTH_TOKEN


print("Loaded Discord")
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def pingu(ctx):
    await ctx.send('NOOT NOOT!')

@bot.group()
async def league(ctx):
    pass

@bot.group()
async def match(ctx):
    pass

@league.command()
async def create(ctx, name):
    await ctx.send(await createLeague(name, ctx.guild))

@league.command()
async def list(ctx):
    message = await listLeagues(ctx.guild)
    await ctx.send(message)

@league.command()
async def recalculate(ctx, league = None, match_id = None):
    message = await recalculateMatch(match_id, league, ctx.guild)
    await ctx.send(message[1])


@league.command()
async def ranking(ctx, name, page = 0):
    message = await printRanking(bot, ctx.guild, name, page)
    await ctx.send(message, allowed_mentions=discord.AllowedMentions(roles=False, users=False, everyone=False))

@league.command()
async def botJoin(ctx):
    await ctx.send("I get to play!!!")
    message = await addPlayerToLeague(bot.user, "civ6", ctx.guild)
    await ctx.send(message)

@league.command()
async def join(ctx, name):
    message = await addPlayerToLeague(ctx.author, name, ctx.guild)
    await ctx.send(message)

@match.command(pass_context=True)
async def list(ctx, league = None):
    if(not league):
        await ctx.send("Please specify a league")
        return
    message = await listMatches( ctx.guild, league)
    if(message[0]):
        mess = await ctx.send(message[1])

@match.command(pass_context=True)
async def register(ctx, league, *members: discord.User):
    message = await registerMatch( ctx.guild, league, members)
    mess = await ctx.send(message[1])
    if(mess and message[0]):
        match = message[2]
        await addMessageToMatch(match, mess.id)
        await mess.add_reaction('\U0001F44D')

@sync_to_async
def addMessageToMatch(match, _id):
    match.message_id = _id
    match.save()
@bot.event
async def on_raw_reaction_add(payload):
    if(payload.message_author_id == bot.user.id):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        users = [str(user.id) async for user in message.reactions[0].users()]
        if(await validate_match_payload(payload, users)):
            await message.reply("Results approved. Calculating results.")
            match = await getMatchFromMessage(payload.message_id)
            m = await finish_match(match)
            await channel.send(m)


@register.error
async def register_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Error: Could not find one or more members mentioned")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Error: The arguments passed were invalid (Do these members all exist?)")
    else:
        await ctx.send("Unexpected error")
        print(error)


def start():
    bot.run(BOT_AUTH_TOKEN)
