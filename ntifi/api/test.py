import os
import api
import asyncio
from dotenv import load_dotenv

fin = api.Jellyfin()

api_key = os.getenv("api_key")
server = os.getenv("server")
sess = fin.auth(token=api_key)
#print(sess)
#token = sess[0]

async def main():
	ws = fin.websocket(server, "discord")
	events = ws.listen()
	await ws.subscribe("SessionsStart", 2000)
	async for message in events:
		if message == None: continue # just ignore if its not playback :(
		print(f"raw message: {list(message)}")
		schemad = message[1]
		print(f"schemad {schemad}")
		if schemad:
			message = message[0] # schema'd!
			print(f"raw schema: {message}")
			print(f"stuff: {message['data']['playState']['positionTicksFormatted']}")
		else:
			print(f"unreachable code reached wtf")
			continue

if __name__ == '__main__':
	asyncio.run(main())