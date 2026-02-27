import json
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
	return formatted

def format_to_schema(api, fp=None):
	"""Takes in a raw api response,
	converts it to fit schema.json schema,
	and writes that to fp (optionally)"""
	try:
		api_resp = json.loads(api)
		#print(api_resp)
		if api_resp['MessageType'] == "ForceKeepAlive": return api # ignore ping-pongs 
		data = api_resp['Data'][0]# if type(api_resp['Data'][0]) is dict else None
		with open(fp, "w") as f:
			json.dump(schema, f, indent=2, ensure_ascii=False)

		if data:
			schema = {
				'messageId': api_resp['MessageId'],
				'data': {
					'playState': {
						'positionTicks': data['PlayState'].get('PositionTicks', None),
						'isPaused': data['PlayState']['IsPaused'],
					},
					'userId': data['UserId'],
					'userName': data['UserName'],
					'lastPaused': data.get('LastPausedDate', None),
					'deviceName': data['DeviceName'],
					'nowPlaying': {
						'name': data['NowPlayingItem']['Name'],
						'id': data['NowPlayingItem']['Id'],
						'totalTicks': data['NowPlayingItem']['RunTimeTicks'],
						'type': data['NowPlayingItem']['Type'],
						# None for episode/season if movie
						'episode': data['NowPlayingItem'].get('IndexNumber', None), # no idea if this works
						'season': data['NowPlayingItem'].get('ParentIndexNumber', None),
						'seasonName': data['NowPlayingItem'].get('SeasonName', None), # season name doesnt exist if its not a show
						'seriesName': data['NowPlayingItem'].get('SeriesName', None), # same for series name apparently?
					},
					'eventType': api_resp['MessageType']
				}
			}
			print(api_resp['MessageType'])
			if fp:
				with open(fp, "w") as f:
					json.dump(schema, f, indent=2, ensure_ascii=False)
			return schema
		return api
	except Exception as e:
		print(e)
		

# print(ticks_to_dt(37408540))
if __name__ == '__main__':
	with open("out.json", "r") as f:
		print(format_to_schema(f.read()))
		#format_to_schema(f.read())