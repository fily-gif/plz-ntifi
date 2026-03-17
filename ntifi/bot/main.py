import os
import api
import asyncio
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv("../.env")
intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
bot_token = os.getenv("bot_token")
api_key = os.getenv("api_key")
server = os.getenv("server")
fin = api.Jellyfin()
token = fin.auth(token=api_key)

target_channel = None
stored_event = ""

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
	global stored_event # apparently we need to do these _inside_ the functions to make them edit the _global_ stored_event/target_channel. huh.
	stored_event = event
	await ctx.response.defer()
	await ws.subscribe(str(event), timing) # str'ing just in case
	#print(event, _event, timing)
	await ctx.send(f"subscribed to {event} with {timing}ms interval!", ephemeral=True)

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def set_channel(ctx, channel: nextcord.TextChannel):
	global target_channel
	global stored_event
	target_channel = channel.id
	_channel = bot.get_channel(target_channel) # ..?
	#print(target_channel, _channel or None)
	await ctx.send(f"set channel to <#{target_channel}>! ({target_channel})")
	await _channel.send("-# this channel has been subscribed to for jellyfin events!")
	#print(channel.id, _channel)

async def _tracking_loop(channel):
	await ws._event.wait()
	async for message in events:
		print(message)
		try:
			if message[1]: # if True
				message = message[0]
				print(message)
				embed = nextcord.Embed(color=int("e0f0e3", 16))
				embed.set_author(name=str(message['data']['nowPlaying']['name']) if message['data']['nowPlaying']['type'] != "Movie" else f"{message['data']['nowPlaying']['name']} - S{message['data']['nowPlaying']['season']}E{message['data']['nowPlaying']['episode']} ~ '{message['data']['nowPlaying']['name']}'", url=f"{server}/web/index.html#/details?id={message['data']['nowPlaying']['id']}")
				embed.add_field(name="paused" if message['data']['playState']['isPaused'] else "playing", value=message['data']['playState']['positionTicksFormatted'])
				embed.set_thumbnail(url=f"{server}/Items/{message['data']['nowPlaying']['id']}/Images/Primary")
				embed.set_footer(text=f"{message['data']['userName']}")
				await channel.send(embed=embed)
			continue
		except Exception as e:
			print(f"AAAAAAAAAA {e}")
			continue

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def start_tracking(ctx):
	global target_channel
	global stored_event
	#print(target_channel)
	channel = bot.get_channel(target_channel)
	print(stored_event or None)
	await channel.send(f"all {stored_event} events will be sent here!!")
	await ws._event.wait() # HACK: another race condition! using internal wait() to wait for websocket to actually connect :fear:
	await ctx.send("-# tracking started!", ephemeral=True) # we have to send something so that discord doesnt show an error
	asyncio.create_task(_tracking_loop(channel)) # apparently this command sometimes(??????) freezes the entire script -> asyncio bullshit go

@bot.slash_command()
@commands.check_any(commands.is_owner())
async def stop(ctx):
	await ctx.send("stopping...", ephemeral=True)
	#AI: boss im tired (clausde helped me specifically with asyncio stuff)
	tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
	for task in tasks:
		task.cancel()
	await asyncio.gather(*tasks, return_exceptions=True)
	await bot.close()

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