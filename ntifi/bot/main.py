import os
import api
import asyncio
import time
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
# NOTE: claude helped me with multi-user-handling-stuff but it shouldnt really matter because im just too tired and the mvp worked:tm: so hhhhhhhhhhhhhhhh blehh
target_channel = None
stored_event = ""
user_messages: dict = {}
user_last_update: dict = {}
MIN_UPDATE_INTERVAL = 0.5

def is_guild_owner():
	def predicate(ctx):
		return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
	return commands.check(predicate)

def build_embed(message: dict) -> nextcord.Embed:
	"""Builds a nextcord.Embed from a formatted schema message dict."""
	now_playing = message['data']['nowPlaying']
	play_state  = message['data']['playState']
	is_paused   = play_state['isPaused']

	color = int("ffcc00", 16) if is_paused else int("77dd77", 16)
	embed = nextcord.Embed(color=color)

	if now_playing['type'] != "Movie":
		author_name = (
			f"{now_playing['seriesName']} - "
			f"S{now_playing['season']}E{now_playing['episode']} "
			f"~ '{now_playing['name']}'"
		)
	else:
		# just the title if its a movie because movies dont have episodes (what!)
		author_name = now_playing['name']

	embed.set_author(
		name=author_name,
		url=f"{server}/web/index.html#/details?id={now_playing['id']}"
	)
	embed.add_field(
		name="paused" if is_paused else "playing",
		value=f"{play_state['positionTicksFormatted']} / {now_playing['totalTicksFormatted']}" # TODO: progress bar
	)
	embed.set_thumbnail(url=f"{server}/Items/{now_playing['id']}/Images/Primary")
	embed.set_footer(text=message['data']['userName'])
	return embed


@bot.slash_command()
async def ping(ctx):
	await ctx.send(f'pong! ({round(bot.latency*1000, 2)})')

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def event_subscribe(ctx, event, timing: int = 1000): # timing is in ms!!
	global stored_event
	stored_event = event
	await ctx.response.defer()
	await ws.subscribe(str(event), timing) # str'ing just in case
	await ctx.send(f"subscribed to {event} with {timing}ms interval!", ephemeral=True)

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def set_channel(ctx, channel: nextcord.TextChannel):
	global target_channel
	target_channel = channel.id
	_channel = bot.get_channel(target_channel)
	await ctx.send(f"set channel to <#{target_channel}>! ({target_channel})")
	await _channel.send("-# this channel has been subscribed to for jellyfin events!")

async def _tracking_loop(channel):
	await ws._event.wait()
	async for message in events:
		print(message)
		try:
			if not message[1]: # we got garbage :(
				continue

			message = message[0]
			print(message)

			user_id = message['data']['userId']
			now = time.monotonic()

			# --- Rate limiting ---
			# If we updated this user's message too recently, drop the event.
			# This keeps us well under Discord's 50 req/s global limit regardless
			# of how frequently Jellyfin fires events or how many users are active.
			# (^^^ thanks claude)
			if (now - user_last_update.get(user_id, 0)) < MIN_UPDATE_INTERVAL:
				continue

			embed = build_embed(message)

			if user_id in user_messages:
				# edit the embed instead of sending a new one
				try:
					await user_messages[user_id].edit(embed=embed)
				except nextcord.NotFound:
					# uh oh something broke! send a new one!
					user_messages[user_id] = await channel.send(embed=embed)
			else:
				user_messages[user_id] = await channel.send(embed=embed)

			user_last_update[user_id] = time.monotonic()

		except Exception as e:
			print(f"AAAAAAAAAA {e}")
			continue

@bot.slash_command()
@commands.check_any(commands.is_owner(), is_guild_owner())
async def start_tracking(ctx):
	global target_channel
	global stored_event
	channel = bot.get_channel(target_channel)
	print(stored_event or None)
	await channel.send(f"all {stored_event} events will be sent here!!")
	await ws._event.wait() # HACK: race condition, wait for websocket to actually connect
	await ctx.send("-# tracking started!", ephemeral=True) # need to send something so discord doesnt throw the user an error
	asyncio.create_task(_tracking_loop(channel)) # use tasks because the code would sometimes freeze?? 

@bot.slash_command()
@commands.check_any(commands.is_owner())
async def stop(ctx):
	await ctx.send("stopping...", ephemeral=True)
	# AI: boss im tired (claude helped me specifically with asyncio stuff)
	tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
	for task in tasks:
		task.cancel()
	await asyncio.gather(*tasks, return_exceptions=True)
	await bot.close()

@bot.event
async def on_ready():
	print(f"logged in as {bot.user}!! ({bot.user.id})")
	print("straight up socketing it")
	global ws
	global events
	ws = fin.websocket(server, "discord")
	events = ws.listen() # idle the connection idling on startup

bot.run(bot_token)