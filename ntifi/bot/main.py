import discord
from discord.ext import commands
from ...config import Discord

intents = discord.Intents.all()
bot = commands.Bot()

@bot.command()
async def ping(ctx):
	await ctx.send('pong')

bot.run