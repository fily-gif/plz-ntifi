import os
import json
import requests
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
	Handles auth and websocket stuff (mainly logging in and capturing events, see `utils.py` for the rest)
	!NOTE: This is a rewrite of the official library because I don't like how it's doing things, and I needed an extremely specific
	!...set of endpoints, so yes, I reinvented the wheel.
	(I don't like the official library.) 
	"""
	def __init__(self, creds:dict=None):
		self.creds = creds or None # optional credentials from an already logged-in state,
		# TODO: implement auth saving for future usage (take inspiration from official api?)
		#(i.e server, token, optional user+pw if that was used instead of token) (note: server returns token when logging in!)
		self.sess = requests.Session()

	def auth(token:str=None, username=None, password=None):
		"""
		Takes in either str(token), or any(`username` and `password`).
		If only token provided (api key), tries to validate it via `GET /System/Info`.
		If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`.
		"""

		# set jellyfin-specific headers, token or none for auth because we're providing our own (unless user provides it!)
		sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": f"MediaBrowser Client=\"{token or None}\", Device=\"Python\", DeviceId=\"PyJfinApi\", Version=\"10.11.6\""})
		token: str # we'll be editing this later to be whatever the hell we got from auth for future requests
		#...(really, all we need from auth is the token for websocket connection, since the flow is auth("sjkdfhjkfg") -> connect() lol)

		# we might as well try to `ping` the root endpoint itself, but this is the "proper"-er way of doing this
		#...also its almost midnight and i want to get just the class rewrite out lol (even if it doesnt work)
		server_is_valid: bool = sess.get(f"{server}/System/Info/Public").status_code == 200
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
				login = sess.post(f"{server}/Users/AuthenticateByName", json={'Username': username, 'Pw': password})
				if login.status_code == 200:
					logs = login.json()
					print(f"logged in as {logs['User']['Name']}!")
					return login.json()['AccessToken'] # because we're feeling nice today
		else:
			# uh oh!
			return # good luck to future me debugging this mess lol what a loser

def auth(token:str=None, username=None, password=None):
	"""Takes in either str(token), or any(`username` and `password`).
	If only token provided (api key), tries to validate it via `GET /System/Info`. on fail, throws and screams.
	If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`. on fail, throws and screams."""
	
	# for persistent sessions across the file
	# TODO: move to global scope? (when moving to classes)
	global sess
	sess = requests.Session()
	sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": "MediaBrowser Client=\"Jellyfin API\", Device=\"Python\", DeviceId=\"sdf\", Version=\"10.11.6\""})
	# is the server even valid?
	server_is_valid: bool = sess.get(f"{server}/System/Info/Public").status_code == 200
	if server_is_valid:
		if token and not (username and password):
			print(f"using token to log in for {server}...")
			token = f'MediaBrowser Token="{token}"'
			sess.headers.update({"Authorization": token})
			try:
				login = sess.get(f"{server}/System/Info") # GET'ing an authorized endpoint
				if login:
					print("logged in!! saving into [conf]...")
					conf.append(token) # TODO: PERSIST!!!!
					return token, login.json()
			except Exception as e:
				print(e)
				#raise "JellyfinAuthException"
		elif not token and (username and password):
			print(f"logging in as {username}...")
			login = sess.post(f"{server}/Users/AuthenticateByName", json={'Username': username, 'Pw': password})
			if login.status_code == 200:
				logs = login.json()
				print(f"logged in as {logs['User']['Name']}!! saving into [conf]...")
				#print(logs)
				conf.append(logs['AccessToken'])
	else: # "everything's on fire and pigs are flying" -my friend
		print("UH OH UH OH UH OH READ BELOW!!!!!!")
		print("THE SERVER DID NOT RETURN ANYTHING ON `/System/Info/Public`!!!!!")
		print("ENSURE THAT IT IS ON AND ACCESSIBLE FROM THE HOST!!!!!")
		print("(bailing out, you are now on your own.)")


if __name__ == '__main__':
	#username = os.getenv("username")
	#password = os.getenv("password")
	#auth(api_key)
	#auth(username=username, password=password)
	pass