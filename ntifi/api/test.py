import os
import api
import asyncio
from dotenv import load_dotenv

fin = api.Jellyfin()

api_key = os.getenv("api_key")
server = os.getenv("server")
sess = fin.auth(token=api_key)
print(sess)
#token = sess[0]

async def main():
	ws = api.JellyfinWS(fin, server, "sdfj")
	conn = await ws.listen()
	print(conn)

if __name__ == '__main__':
	asyncio.run(main())