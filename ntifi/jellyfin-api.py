from config import *
import json
import requests

global storage
def auth(token:str=None, username=None, password=None):
	# Takes in either `token`, or (`username` AND `password`).
	# ...and uses Magic to Authenticate the User.
	
	sess = requests.Session()
	if token and not all((username, password)): # why is python like that.
		print("using token to log in...")
		token = f'MediaBrowser Token="{token}"'
		sess.headers.update({'User-Agent': "fily-github-com/1.0", "Authorization": token})
		try:
			test = sess.get(f"{Jellyfin.server}/System/Info")
			print(test.text)
		except Exception as e:
			if "No scheme supplied" in e:
				Jellyfin.server = f"https://{Jellyfin.server}" # assuming https because why would it Not be https..?
			print(e)
			#raise "JellyfinAuthException"
	pass

auth(Jellyfin.api_key)