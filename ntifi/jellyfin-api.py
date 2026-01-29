from config import *
import json
import requests
server = Jellyfin.server if Jellyfin.server.startswith(("http://", "https://")) else f"https://{Jellyfin.server}"
#* assuming https

def auth(token:str=None, username=None, password=None):
	# Takes in either `token`, or (`username` AND `password`).
	# If only token provided (api key), tries to validate it via `GET /System/Info`. on fail, throws and screams.
	# If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`. on fail, throws and screams.
	
	# for persistent sessions across the file
	# TODO: move to global scope?
	sess = requests.Session()
	# is the server even valid?
	server_is_valid: bool = sess.get(f"{server}/System/Info/Public").status_code == 200
	if server_is_valid:
		if token and not (username and password):
			print(f"using token to log in for {server}...")
			token = f'MediaBrowser Token="{token}"'
			sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": token})
			try:
				test = sess.get(f"{server}/System/Info")
				print(test.json())
			except Exception as e:
				print(e)
				#raise "JellyfinAuthException"
		pass

auth(Jellyfin.api_key)