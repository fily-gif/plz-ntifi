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
		print(f"aaaa\n{message}\nAAAA")

if __name__ == '__main__':
	asyncio.run(main())