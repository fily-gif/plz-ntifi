from config import *
import json
import requests

global storage
def auth(token:str=None, username=None, password=None):
	# Takes in either `token`, or (`username` AND `password`).
	# If only token provided (api key), tries to validate it via `GET /System/Info`. on fail, throws and screams.
	# If only (`username` AND `password`) provided, logs in via `GET /Users/AuthenticateByName`. on fail, throws and screams.
	
	# for persistent sessions across the file
	# TODO: move to global scope?
	sess = requests.Session()
	# is the server even valid?
	server_is_valid: bool = False
	server_is_valid = True if sess.get(f"{Jellyfin.server}/System/Info/Public").status_code == 200 else False
	if server_is_valid:
		if token and not (username and password): # why is python like that.
			print("using token to log in...")
			token = f'MediaBrowser Token="{token}"'
			sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": token})
			try:
				test = sess.get(f"{Jellyfin.server}/System/Info")
				print(test.json())
			except Exception as e:
				#! VVV broken!!
				# if "No scheme supplied" in e:
				# 	Jellyfin.server = f"https://{Jellyfin.server}" # assuming https because why would it Not be https..?
				# 	raise
				print(e)
				#raise "JellyfinAuthException"
		pass

auth(Jellyfin.api_key)