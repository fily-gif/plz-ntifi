import json
from datetime import timedelta, datetime

def ticks_to_dt(ticks:int):
	# takes in ticks from
	#...api_response['Data']['PlayState']['PositionTicks']
	#...and converts it into a datetime object  
	#...(jellyfin ticks are 1ms)
	seconds = ticks / 10_000_000 # til python support that lol
	delta = timedelta(seconds=seconds)

	# str-ify and do funny cat face for .mmm
	formatted = str(delta)[:-3]
	return formatted

def format_to_schema(api, fp=None):
	# takes in a raw api response,
	#...converts it to fit schema.json schema,
	#...and writes that to fp (optionally)
	api_resp = json.loads(api)
	data = api_resp['Data'][0]

	schema = {
		'messageId': api_resp['MessageId'],
		'data': {
			'playState': {
				'positionTicks': data['PlayState'].get('PositionTicks', -1),
				'isPaused': data['PlayState']['IsPaused'],
			},
			'userId': data['UserId'],
			'userName': data['UserName'],
			'lastPaused': data.get('LastPausedDate', ""),
			'deviceName': data['DeviceName'],
			'nowPlaying': {
				'name': data['NowPlayingItem']['Name'],
				'id': data['NowPlayingItem']['Id'],
				'totalTicks': data['NowPlayingItem']['RunTimeTicks'],
				'type': data['NowPlayingItem']['Type'],
				# -1 for episode/season if movie
				'episode': data['NowPlayingItem'].get('IndexNumber', -1), # no idea if this works
				'season': data['NowPlayingItem'].get('ParentIndexNumber', -1),
				'seasonName': data['NowPlayingItem']['SeasonName'],
				'seriesName': data['NowPlayingItem']['SeriesName'],
			}
		}
	}

	if fp:
		with open(fp, "w") as f:
			json.dump(schema, f)
	return schema

print(ticks_to_dt(37408540))