import sys
import json
import traceback
from datetime import timedelta, datetime

def ticks_to_dt(ticks:int):
	"""Takes in ticks from
	api_response['Data']['PlayState']['PositionTicks']
	and converts it into a datetime object  
	(jellyfin ticks are 1ms)"""
	seconds = ticks / 10_000_000 # til python support that lol
	delta = timedelta(seconds=seconds)

	# str-ify and do funny cat face for .mmm
	formatted = str(delta)[:-3]
	return formatted # NOTE: yes this means that we cant do further datetime operation with this unless
	#we're parsing this again, but the thing is, we dont need to anymore.

def format_to_schema(api, fp=None):
	"""Takes in a raw api response,
	converts it to fit schema.json schema,
	and writes that to fp (optionally)"""
	# TODO: TEST NOWPLAYING.TYPE TYPES TO SEE HOW DIFFERENT THE API RESPONSE IS
	try:
		print("got schema request!")
		api_resp = json.loads(api)
		results = []
		#print(api_resp)
		data = api_resp['Data']
		print(data)

		for data in api_resp['Data']:  # iterate ALL sessions, not just [0]
			if not data.get('NowPlayingItem'):
				continue  # skip idle sessions

			schema = {
				'messageId': api_resp['MessageId'],
				'data': {
					'playState': {
						'positionTicks': data['PlayState']['PositionTicks'],
						'positionTicksFormatted': ticks_to_dt(data['PlayState']['PositionTicks']),
						'isPaused': data['PlayState']['IsPaused'],
					},
					'userId': data['UserId'],
					'userName': data['UserName'],
					'lastPaused': data.get('LastPausedDate', None),
					'deviceName': data['DeviceName'],
					'nowPlaying': {
						'name': data['NowPlayingItem']['Name'], # name of the episode
						'id': data['NowPlayingItem']['Id'],
						'totalTicks': data['NowPlayingItem']['RunTimeTicks'],
						'totalTicksFormatted': ticks_to_dt(data['NowPlayingItem']['RunTimeTicks']),
						'type': data['NowPlayingItem']['Type'], # realistically, we only care about Episode, Movie, Season, Series
						# None for episode/season if Movie
						'episode': data['NowPlayingItem'].get('IndexNumber', None), # no idea if this works
						'season': data['NowPlayingItem'].get('ParentIndexNumber', None),
						'seasonName': data['NowPlayingItem'].get('SeasonName', None), # season name doesnt exist if its not a Series?
						'seriesName': data['NowPlayingItem'].get('SeriesName', None), # same for series name apparently?
					},
					'eventType': api_resp['MessageType']
				}
			}
			results.append(schema)

		if fp and results:
			with open(fp, "w") as f:
				json.dump(results, f, indent=2, ensure_ascii=False)
		
		print(results)
		return results or None  # None if no active sessions 

	except Exception as e:
		traceback.print_exc(file=sys.stdout)
		for line in traceback.format_tb(e.__traceback__):
			print(f"ERROR: {line}", end="")

# print(ticks_to_dt(37408540))
if __name__ == '__main__':
	with open("out.json", "r") as f:
		print(format_to_schema(f.read()))
		#format_to_schema(f.read())