import os
import nextcord
from nextcord.ext import commands
#from discord import app_commands # slash commands
from dotenv import load_dotenv
import api

load_dotenv("../.env")
intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
bot_token = os.getenv("bot_token")
api_key = os.getenv("api_key")
fin = api.Jellyfin()
token = fin.auth(token=api_key)
print(token)

@bot.slash_command()
async def ping(ctx):
	await ctx.send('pong')

@bot.slash_command()
async def test(ctx):
	await ctx.defer()
	await ctx.reply("sdfsdf")

@bot.event
async def on_ready():
	print(f"logged in as {bot.user}!! ({bot.user.id})")
	

bot.run(bot_token)