import os
import nextcord
from nextcord.ext import commands
#from discord import app_commands # slash commands
from dotenv import load_dotenv

load_dotenv()
intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
token = os.getenv("bot_token")

@bot.slash_command()
async def ping(ctx):
	await ctx.send('pong')

@bot.event
async def on_ready():
	print(f"logged in as {bot.user}!! ({bot.user.id})")

bot.run(token)