from audioop import add
from venv import create
import discord
from discord.ext import commands
from .django_commands import createLeague, listLeagues, printRanking, addPlayerToLeague

print("Loaded Discord")
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.group()
async def league(ctx):
    pass

@league.command()
@commands.has_permissions(administrator=True)
async def create(ctx, name):
    await ctx.send(await createLeague(name, ctx.guild))

@league.command()
async def list(ctx):
    message = await listLeagues(ctx.guild)
    await ctx.send(message)

@league.command()
async def ranking(ctx, name, page = 0):
    message = await printRanking(bot, ctx.guild, name, page)
    await ctx.send(message, allowed_mentions=discord.AllowedMentions(roles=False, users=False, everyone=False))

@league.command()
async def join(ctx, name):
    message = await addPlayerToLeague(ctx.author, name, ctx.guild)
    await ctx.send(message)



def start():
    bot.run('XXX')
