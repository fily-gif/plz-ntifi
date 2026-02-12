#! NOTE: THIS DOES NOT WORK.
#! DO NOT USE THIS!!!!!!!!!!!!!!!!!

import jellyfin #auth, websocket

creds = {'server': 'ip/url here', 'username': None, 'password': None, 'token': 'sdfbvfg'}
# prefers token over username
#creds = jellyfin.auth(token='sdfjkk') #{'server': 'ip/url here', 'username': None, 'password': None, 'token': 'sdfbvfg'}
fin = Jellyfin(creds) # looks messy, oh well
ws = jellyfin.websocket(creds[0], "rgsdfjdvfg") #server, device_id

# async!
async def main():
	conn = ws.connect()
	# im bad at naming variables lol
	events = ws.subscribe("event", 1000) #event, timing (ms)
	async for message in evens: # returns the custom schema (much cleaner and better than whatever the hell the api returns)
		match message:
			case "event1":
				print("sdfjlnvjknfgnbjkfg")
			case _:
				print("aaaaaaaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")