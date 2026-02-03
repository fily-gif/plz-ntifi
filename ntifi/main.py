from config import Jellyfin
from jellyfin_api import auth
import json
from websockets.sync.client import connect

sess = auth(Jellyfin.api_key)
token = sess[0] # formatted api key for http api
rejson = sess[1] # system/info return
server = Jellyfin.server.replace("https://", "wss://")+f"/socket?api_key={Jellyfin.api_key}&device_id=sdfsdf" # oh man i sure do hope nothing breaks!

def main(server):
	with connect(server) as ws:
		ws.send(json.dumps({"MessageType": "SessionsStart", "Data": "0,2000" }))
		# subscribing to SessionsStart with initialdelay 0, interval 2000
		# ...this means that it sends as soon as possible (0), and then "polls" every 2000ms (god i hate jellyfin api)
		while True:
			message = ws.recv() # wait for message
			print(f"Received message: {message}") # got it!!
			mes = json.loads(message)
			match mes['MessageType']:
				case "Sessions":
					with open("out.json", "w") as f:
						json.dump(message, f, indent=4, ensure_ascii=True)
				case "ForceKeepAlive": # will forcefully close if not pinged back
					ws.send(json.dumps({"MessageType": "KeepAlive"})) # ping back
					print("pong!!")
				case "KeepAlive": # BUG: ws.recv apparently returns whatever we sent??
					pass # we sent this, move on
				case _:
					print(f"got {mes} (unhandled!)")

if __name__ == "__main__":
	main(server)