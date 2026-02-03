import json
from datetime import timedelta, datetime

def ticks_to_dt(ticks:int=0):
	# takes in ticks from
	#...api_response['Data']['PlayState']['PositionTicks']
	#...and converts it into a datetime object  
	#...(jellyfin ticks are 1ms)
	seconds = ticks / 10_000_000 # til python support that lol
	delta = timedelta(seconds=seconds)

	# str-ify and do funny cat face for .mmm
	formatted = str(delta)[:-3]
	return formatted


print(ticks_to_dt(37408540))