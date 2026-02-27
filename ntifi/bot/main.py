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

_channel = ""
_event = ""

def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

@bot.slash_command()
async def ping(ctx):
	await ctx.send(f':pong: pong! ({round(bot.latency*1000, 2)})')

@bot.slash_command()
async def event_subscribe(ctx, event, timing:int="1000"): # timing is in ms!!
	await ctx.response.defer()
	await ws.subscribe(f"{event}", timing) # str'ing just in case
	await ctx.send(f"subscribed to {event} with {timing}ms interval!", ephemeral=True)
	_event = event
	

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def set_channel(ctx, channel: nextcord.TextChannel):
	_channel = channel.id
	await ctx.send(f"set channel to <#{channel.id}>! ({channel.id})")

@bot.slash_command()
async def start_tracking(ctx):
	await ctx.send(f"all {_event} events will be sent here!!")
	async for message in events:
		await ctx.send(str(message))

@bot.event
async def on_ready():
	print(f"logged in as {bot.user}!! ({bot.user.id})")
	print("straight up socketing it")
	# for use in the rest of the code
	global ws
	global events
	ws = fin.websocket(server, "discord")
	global events
	events = ws.listen() # idling the connection on start
	

bot.run(bot_token)