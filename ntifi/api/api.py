import os
import json
import utils
import asyncio
import requests
from websockets.asyncio.client import connect
from dotenv import load_dotenv
load_dotenv()
server: str = (s := os.getenv("server")) and (s if s.startswith(("http://", "https://")) else f"https://{s}")
#* assuming https if no schema
#! !!!!NOTE!!!! I USED AI FOR `server` BECAUSE IM TOO STUPID
api_key = os.getenv("api_key")
ws_server = server.replace("https://", "wss://")+f"/socket?api_key={api_key}&device_id=fjapi-ws"
conf: list = [] # TODO: save in a file?

class Jellyfin:
	"""
	The Jellyfin API class.
	Handles auth and websocket stuff (in JellyfinWS) (mainly logging in and capturing events, see `utils.py` for the rest)
	!NOTE: This is a rewrite of the official library because I don't like how it's doing things, and I needed an extremely specific
	!...set of endpoints, so yes, I reinvented the wheel.
	(I don't like the official library.) 
	"""
	def __init__(self, creds:dict=None):
		self.creds = creds or None # optional credentials from an already logged-in state,
		# TODO: implement auth saving for future usage (take inspiration from official api?)
		#(i.e server, token, optional user+pw if that was used instead of token) (note: server returns token when logging in!)
		self.sess = requests.Session()

	def auth(self, token:str=None, username=None, password=None):
		"""
		Takes in either str(token), or any(`username` and `password`).
		If only token provided (api key), tries to validate it via `GET /System/Info`.
		If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`.
		"""

		# set jellyfin-specific headers, token or none for auth because we're providing our own (unless user provides it!)
		self.sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": f"MediaBrowser Client=\"{token or None}\", Device=\"Python\", DeviceId=\"PyJfinApi\", Version=\"10.11.6\""})
		token: str # we'll be editing this later to be whatever the hell we got from auth for future requests
		#...(really, all we need from auth is the token for websocket connection, since the flow is auth("sjkdfhjkfg") -> connect() lol)

		# we might as well try to `ping` the root endpoint itself, but this is the "proper"-er way of doing this
		#...also its almost midnight and i want to get just the class rewrite out lol (even if it doesnt work)
		server_is_valid: bool = self.sess.get(f"{server}/System/Info/Public").status_code == 200
		if server_is_valid:
			if token and not (username and password):
				print(f"using token to log in for {server}!") # FIXME: change all prints to logger!!
				try:
					login = self.sess.get(f"{server}/System/Info") # GETing an authed endpoint
					if login: # did we pass the test?
						print("logged in!") # TODO: print who we are?
						return token, login.json() # returning token for future reference, as well as json for debugging/other info (system/info has some useful stuff!)
				except Exception as e:
					# oh no.
					print(e)

			elif not token and (username and password): # user login
				print(f"logging in as {username}...")
				login = self.sess.post(f"{server}/Users/AuthenticateByName", json={'Username': username, 'Pw': password})
				if login.status_code == 200:
					logs = login.json()
					print(f"logged in as {logs['User']['Name']}!")
					return login.json()['AccessToken'] # because we're feeling nice today
		else:
			# uh oh!
			return # good luck to future me debugging this mess lol what a loser

	def websocket(self, server, device_id):
		return JellyfinWS(self, server, device_id)

class JellyfinWS:
	"""
	Jellyfin WebSocket class.
	There is absolutely no scenario in which this should be used directly,
	and it most likely doesnt work on its own.
	By rawdogging JellyfinWS, you agree to never ever _EVER_ complain
	about your code not working.
	(why would you even use this entire file on its own??? its a part of plz-notifi)
	"""
	#! NOTE: AI USAGE DISCLOSURE:
	#! I GOT SOME HELP FROM AN LLM
	#! BECAUSE IM TOO STUPID FOR ALL OF THIS
	#! FANCY ASYNCIO STUFF!!!
	def __init__(self, jellyfin: Jellyfin, server: str, device_id: str):
		self.jellyfin = jellyfin
		# assuming https because meh
		self.server = server.replace("https://", "wss://")+f"/socket?api_key={api_key}&device_id={device_id}"
		self.device_id = device_id
		self._event = asyncio.Event() # "connected event" event
		self._queue = asyncio.Queue()
	
	def schema(self, input): # lol
		return utils.format_to_schema(input)

	async def _listen(self, schema_format:bool=True): # yea i'd like a schema thanks
		async with connect(self.server) as ws:
			print(f"connecting to {server.replace("https", "wss",)}")
			# HACK: :(
			self._ws = ws # expose websocket for subscribe()
			self._event.set() # signal that we're ready
			# TODO: load in the message and do keepalive stuff! (also check for those)
			async for message in ws:
				temp = json.loads(message)
				if temp['MessageType'] == "ForceKeepAlive": # ping
					await ws.send(json.dumps({"MessageType": "KeepAlive"})) # pong
					continue
				if temp['MessageType'] == "KeepAlive": # we sent this
					continue
				#print(message)
				await self._queue.put(self.schema(message)) if schema_format else await self._queue.put(message)
	
	def listen(self):
		"""
		Connects to self.server (as defined in __init__().)
		"""
		asyncio.create_task(self._listen())
		return self._iter()

	async def _iter(self):
		while True:
			yield await self._queue.get()

	async def subscribe(self, event_type: str or list, interval_ms: int):
		"""
		Subscribes to an event with interval_ms interval.
		For a list of all events, find them yourself (for now) (sorry!)
		"""
		# TODO: make an enum(?) of all possible ws events
		await self._event.wait() # im waiting and waiting and waiting and waiting for you 🗣️🗣️🗣️🗣️
		if type(event_type) == list:
			for event in event_type:
				await self._ws.send(json.dumps({"MessageType": event_type, "Data": f"0,{interval_ms}" }))
				print(f"subscribed to events {event_type}")
		else:
			await self._ws.send(json.dumps({"MessageType": event_type, "Data": f"0,{interval_ms}" }))
			print(f"subscribed to event {event_type}")

if __name__ == '__main__':
	#username = os.getenv("username")
	#password = os.getenv("password")
	#auth(api_key)
	#auth(username=username, password=password)
	pass