from config import *
import json
import requests
server: str = Jellyfin.server if Jellyfin.server.startswith(("http://", "https://")) else f"https://{Jellyfin.server}"
#* assuming https if no schema

conf: list = []
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

#auth(Jellyfin.api_key)
auth(username=Jellyfin.username, password=Jellyfin.password)