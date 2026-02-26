import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import api

load_dotenv("../.env")
intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
bot_token = os.getenv("bot_token")
api_key = os.getenv("api_key")
server = os.getenv("server")
fin = api.Jellyfin()
token = fin.auth(token=api_key)

def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

@bot.slash_command()
async def ping(ctx):
	await ctx.send('pong')

@bot.slash_command()
async def event_subscribe(ctx, event, timing:int="1000"): # timing is in ms!!
	await ctx.response.defer()
	await ws.subscribe("event", timing)
	await ctx.followup.respond(f"subscribed to {event} with {timing}ms interval!", ephemeral=True)

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def set_channel(ctx, channel: nextcord.TextChannel):
	await ctx.respond("sdfjdf")

@bot.event
async def on_ready():
	print(f"logged in as {bot.user}!! ({bot.user.id})")
	print("straight up socketing it")
	ws = fin.websocket(server, "discord")
	events = ws.listen() # idling the connection on start
	# for use in the rest of the code
	global ws
	global events
	

bot.run(bot_token)