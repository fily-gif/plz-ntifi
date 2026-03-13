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
@commands.check_any(commands.is_owner(), is_guild_owner())
async def event_subscribe(ctx, event, timing:int="1000"): # timing is in ms!!
	await ctx.response.defer()
	await ws.subscribe(str({event}), timing) # str'ing just in case
	print(event, _event, timing)
	await ctx.send(f"subscribed to {event} with {timing}ms interval!", ephemeral=True)
	_event = event
	print(event, _event, timing)
	

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def set_channel(ctx, channel: nextcord.TextChannel):
	_channel = channel.id
	await ctx.send(f"set channel to <#{channel.id}>! ({channel.id})")
	await _channel.send("this channel has been subscribed to for jellyfin events!")
	#print(channel.id, _channel)

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def start_tracking(ctx):
	#print(ctx)
	#print(dir(ctx))
	#print(dir(ctx.send))
	channel = bot.get_channel(_channel)
	await channel.send(f"all {_event} events will be sent here!!") # FIXME: _event is empty? (not even None...)
	async for message in events:
		message = message[0]
		print(message)
		embed = nextcord.embed(title="Jellyfin", color=nextcord.Colour.greyple)
		embed.add_field("test", message['data']['nowPlaying']['name'])
		#await ctx.channel.send(list(message[0])) # we dont want it to reply to the initial message lol

@bot.slash_command()
@commands.check_any(commands.is_owner())
async def stop(ctx):
	await ctx.send("stopping...", ephemeral=True)
	await bot.close() # close the connection
	exit(0) # explicit 0 just in case

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