# AI: claude was used to rewrite the discord bot for slack.
import os
import sys
# python imports are a mess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api"))
import api
import time
import asyncio
from dotenv import load_dotenv
# god i hate slack api (especially python)
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

load_dotenv()
server = os.getenv("server")
api_key = os.getenv("api_key")
slack_bot = os.getenv("slack_bot")
slack_app = os.getenv("slack_app")
fily = os.getenv("slack_owner")
fin = api.Jellyfin()
token = fin.auth(token=api_key)
app = AsyncApp(token=slack_bot)
target_channel = None
stored_event = ""
user_threads: dict = {} # user_id -> {"thread_ts", "status_ts", "media_id", "last_activity"}
user_last_update: dict = {}

upd_interval = 0.5
inactive_timeout = 1800 # seconds

def build_title(now_playing: dict) -> str:
	if now_playing['type'] != "Movie":
		return (
			f"{now_playing['seriesName']} - "
			f"S{now_playing['season']}E{now_playing['episode']} "
			f"~ '{now_playing['name']}'"
		)
	return now_playing['name']

def build_blocks(message: dict) -> tuple[list, str]:
	now_playing = message['data']['nowPlaying']
	play_state  = message['data']['playState']
	is_paused   = play_state['isPaused']

	color = "ffcc00" if is_paused else "77dd77"
	title = build_title(now_playing)
	status = "paused" if is_paused else "playing"
	progress = f"{play_state['positionTicksFormatted']} / {now_playing['totalTicksFormatted']}" # TODO: progress bar
	item_url = f"{server}/web/index.html#/details?id={now_playing['id']}"
	thumb_url = f"{server}/Items/{now_playing['id']}/Images/Primary"

	blocks = [
		{
			"type": "section",
			"text": {"type": "mrkdwn", "text": f"*<{item_url}|{title}>*\n{status}: {progress}"},
			"accessory": {"type": "image", "image_url": thumb_url, "alt_text": title},
		},
		{
			"type": "context",
			"elements": [{"type": "mrkdwn", "text": message['data']['userName']}],
		},
	]
	fallback_text = f"{title} - {status} ({progress})"
	# HACK: embed color stripe thing
	attachments = [{"color": color, "blocks": blocks}]
	return attachments, fallback_text


@app.command("/ntifi-ping")
async def ping(ack, respond, client):
	await ack() # bolt.py is stupid.
	start = time.monotonic()
	await client.api_test()
	latency = (time.monotonic() - start) * 1000
	await respond(f"pong! ({round(latency, 2)}ms)")

@app.command("/ntifi-subscribe")
async def event_subscribe(ack, respond, command, client):
	await ack()
	global stored_event
	args = command["text"].split()
	event = args[0] if len(args) > 0 else "SessionsStart"
	timing = int(args[1]) if len(args) > 1 else 750 # ms
	stored_event = event
	await ws.subscribe(str(event), timing) # str'ing just in case
	await respond(f"subscribed to {event} with {timing}ms interval!", )

async def _tracking_loop(client):
	await ws._event.wait()
	async for messages in events:
		print(messages)
		try:
			# format_to_schema returns None in two cases:
			#   1. no NowPlayingItem (e.g. SessionsStart with no active media)
			#   2. an exception was raised inside it
			# Both are non-actionable here, so skip instead of crashing on message[1].
			if messages is None:
				continue

			if not messages: # we got garbage :(
				continue

			for message in messages:
				print(message)

				user_id = message['data']['userId']
				now = time.monotonic()

				# rating that limit
				if (now - user_last_update.get(user_id, 0)) < upd_interval:
					continue

				media_id = message['data']['nowPlaying']['id']
				thread = user_threads.get(user_id)

				# start a new thread if: we've never seen this user, they switched media,
				# or they've been quiet long enough that we treat this as a new watch session.
				needs_new_thread = (
					thread is None
					or thread['media_id'] != media_id
					or (now - thread['last_activity']) > inactive_timeout
				)

				if needs_new_thread:
					title = build_title(message['data']['nowPlaying'])
					start_text = f"_{message['data']['userName']}_ started watching *{title}*!"
					try:
						start_resp = await client.chat_postMessage(channel=target_channel, text=start_text)
					except Exception as e:
						print(f"AAAAAAAAAA {e}")
						continue
					thread = {"thread_ts": start_resp["ts"], "status_ts": None, "media_id": media_id, "last_activity": now}
					user_threads[user_id] = thread
				else:
					thread['last_activity'] = now

				attachments, fallback_text = build_blocks(message)

				if thread['status_ts']:
					# edit the status message in place instead of sending a new one
					try:
						await client.chat_update(channel=target_channel, ts=thread['status_ts'], text=fallback_text, attachments=attachments)
					except Exception:
						# uh oh
						resp = await client.chat_postMessage(channel=target_channel, thread_ts=thread['thread_ts'], text=fallback_text, attachments=attachments)
						thread['status_ts'] = resp['ts']
				else:
					resp = await client.chat_postMessage(channel=target_channel, thread_ts=thread['thread_ts'], text=fallback_text, attachments=attachments)
					thread['status_ts'] = resp['ts']

				user_last_update[user_id] = time.monotonic()

		except Exception as e:
			print(f"AAAAAAAAAA {e}")
			continue

@app.command("/ntifi-track")
async def start_tracking(ack, respond, command, client):
	await ack()
	global target_channel
	if target_channel is None:
		target_channel = command["channel_id"]
	print(stored_event or None)
	await client.chat_postMessage(channel=target_channel, text=f"all {stored_event or 'SessionsStart'} events will be sent here!!")
	await ws._event.wait() # HACK: race condition, wait for websocket to actually connect
	await respond("tracking started!")
	asyncio.create_task(_tracking_loop(client)) # use tasks because the code would sometimes freeze??

@app.command("/ntifi-stop")
async def stop(ack, respond, command, client):
	await ack()
	if command["user_id"] != fily:
		await respond("you're not authorized to do that!")
		return

	await respond("stopping...")
	tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
	for task in tasks:
		task.cancel()
	await asyncio.gather(*tasks, return_exceptions=True)
	await socket_handler.close_async()

async def main():
	global ws, events, socket_handler
	print("straight up socketing it")
	auth = await app.client.auth_test()
	print(f"logged in as {auth['user']}!! ({auth['user_id']})")
	ws = fin.websocket(server, "slack")
	events = ws.listen()
	socket_handler = AsyncSocketModeHandler(app, slack_app)
	await socket_handler.start_async()

if __name__ == "__main__":
	asyncio.run(main())
