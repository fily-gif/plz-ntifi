import os
import json
import asyncio
import logging
import requests
from dotenv import load_dotenv
from . import utils
from websockets.asyncio.client import connect
load_dotenv()
server: str = (s := os.getenv("server")) and (s if s.startswith(("http://", "https://")) else f"https://{s}")
#* assuming https if no schema
#! !!!!NOTE!!!! I USED AI FOR `server` BECAUSE IM TOO STUPID
api_key = os.getenv("api_key")
ws_server = server.replace("https://", "wss://")+f"/socket?api_key={api_key}&device_id=fjapi-ws"
conf: list = [] # TODO: save in a file?

handle = logging.StreamHandler()
logger = logging.getLogger(__name__)
fmt = "[%(levelname)s] (%(asctime)s) %(filename)s:%(funcName)s:%(lineno)d    %(message)s"
logging.basicConfig(level=logging.INFO, handlers=[handle])

#! https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/
class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

handle.setFormatter(CustomFormatter(fmt))

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
		# TODO: implement auth caching for future usage (take inspiration from official api?)
		#(i.e server, token, optional user+pw if that was used instead of token) (note: server returns token when logging in!)
		self.sess = requests.Session()

	def auth(self, token:str=None, username=None, password=None):
		"""
		Takes in either str(token), or any(`username` and `password`).
		If only token provided (api key), tries to validate it via `GET /System/Info`.
		If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`.
		"""

		# set jellyfin-specific headers, token or none for auth because we're providing our own (unless user provides it!)
		self.sess.headers.update({'User-Agent': "com.fily.github/1.0; plz-ntifi/1.0", "Authorization": f"MediaBrowser Client=\"{token or None}\", Device=\"Python\", DeviceId=\"PyJfinApi\", Version=\"10.11.6\""})
		token: str # we'll be editing this later to be whatever the hell we got from auth for future requests
		#...(really, all we need from auth is the token for websocket connection, since the flow is auth("sjkdfhjkfg") -> connect() lol)

		# check if the server is valid by simply requesting a public endpoint and expecting 200
		server_is_valid: bool = self.sess.get(f"{server}/System/Info/Public").status_code == 200
		if server_is_valid:
			if token and not (username and password):
				logger.warn(f"using token to log in for {server}!") # FIXME: change all prints to logger!!
				try:
					login = self.sess.get(f"{server}/System/Info") # GETing an authed endpoint
					if login: # did we pass the test?
						logger.info("logged in!") # TODO: print who we are?
						return token, login.json() # returning token for future reference, as well as json for debugging/other info (system/info has some useful stuff!)
				except Exception as e:
					# oh no.
					logger.critical(e)

			elif not token and (username and password): # user login
				logger.info(f"logging in as {username}...")
				login = self.sess.post(f"{server}/Users/AuthenticateByName", json={'Username': username, 'Pw': password})
				if login.status_code == 200:
					logs = login.json()
					logger.info(f"logged in as {logs['User']['Name']}!")
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

	# TODO: https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Session/SessionMessageType.cs
	def __init__(self, jellyfin: Jellyfin, server: str, device_id: str):
		self.jellyfin = jellyfin
		# Allow larger Jellyfin payloads (e.g. Sessions snapshots) than websockets' 1 MiB default.
		max_size_env = os.getenv("ws_max_size_bytes", "4194304")
		try:
			self.ws_max_size = None if max_size_env.lower() == "none" else int(max_size_env)
		except ValueError:
			self.ws_max_size = 4194304
		# normalize HTTP(S) to WS(S) and avoid accidental double slashes
		server = server.rstrip("/")
		if server.startswith("https://"):
			server = server.replace("https://", "wss://", 1)
		elif server.startswith("http://"):
			server = server.replace("http://", "ws://", 1)
		elif not server.startswith(("ws://", "wss://")):
			server = f"wss://{server}"

		self.server = f"{server}/socket?api_key={api_key}&device_id={device_id}"
		self.device_id = device_id
		self._event = asyncio.Event() # "connected event" event
		self._queue = asyncio.Queue()
		self._ws = None
		self._subscriptions: list[tuple[str, int]] = []
	
	def schema(self, input): # lol
		return utils.format_to_schema(input, "aa.json")

	async def _send_subscription(self, event_type: str, interval_ms: int):
		if not self._ws:
			raise RuntimeError("websocket is not connected")
		await self._ws.send(json.dumps({"MessageType": event_type, "Data": f"0,{interval_ms}"}))

	async def _listen(self, schema_format:bool=True): # yea i'd like a schema thanks
		while True:
			try:
				logger.warning(f"connecting to {self.server}")
				async with connect(self.server, max_size=self.ws_max_size) as ws:
					self._ws = ws # expose websocket for subscribe()
					self._event.set() # signal that we're ready (-> required for subscribe() to function since we're async)
					logger.info("connected!")

					# Re-apply any existing subscriptions after reconnect.
					for event_type, interval_ms in self._subscriptions:
						await self._send_subscription(event_type, interval_ms)
						logger.info(f"re-subscribed to event {event_type} with interval of {interval_ms}ms")

					async for message in ws:
						try:
							temp = json.loads(message)
						except Exception:
							logger.exception("failed to decode websocket message")
							continue

						msg_type = temp.get("MessageType")
						if msg_type == "ForceKeepAlive": # ping
							await ws.send(json.dumps({"MessageType": "KeepAlive"})) # pong
							continue
						if msg_type == "KeepAlive": # we sent this
							continue

						logger.warning(message)
						await self._queue.put(self.schema(message)) if schema_format else await self._queue.put(message)
			except Exception:
				self._event.clear()
				self._ws = None
				logger.exception("websocket listener crashed; retrying in 2s")
				await asyncio.sleep(2)
	
	def listen(self):
		"""
		Connects to self.server (as defined in __init__().)
		"""
		self._task = asyncio.create_task(self._listen())
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
		# WARN: LIST IS UNUSED AND IS KEPT JUST IN CASE. THEREFORE, IT IS UNTESTED!
		events = event_type if isinstance(event_type, list) else [event_type]
		for event in events:
			if (event, interval_ms) not in self._subscriptions:
				self._subscriptions.append((event, interval_ms))
			await self._send_subscription(event, interval_ms)
			logger.info(f"subscribed to event {event} with interval of {interval_ms}ms")

if __name__ == '__main__':
	#username = os.getenv("username")
	#password = os.getenv("password")
	#auth(api_key)
	#auth(username=username, password=password)
	#logging.critical("asdfdsd")
	pass