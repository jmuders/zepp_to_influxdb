import datetime
import json
import requests


class StressDataExtractor:

    def __init__(self, auth_info, query_duration=1):
        self.auth_info = auth_info
        self.query_duration = query_duration

    def extract(self):
        ''' Retrieve stress level information
        '''
        rows = []
        
        ''' calculate the times that the api query should check between
        '''
        today = datetime.datetime.today()
        today_end = datetime.datetime.combine(today, datetime.datetime.max.time()) 

        query_start_d = today - datetime.timedelta(days=self.query_duration)
        # Make it midnight  - the api doesn't seem to like mid-day queries
        query_start = datetime.datetime.combine(query_start_d, datetime.datetime.min.time())
        
        
        print("Retrieving stress data")
        band_data_url=f"https://api-mifit.zepp.com/users/{self.auth_info['token_info']['user_id']}/events"
        headers={
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        data={
            'from': query_start.strftime('%s000'),
            'to': today_end.strftime('%s000'),
            "eventType": "all_day_stress",
            "limit": 1000
        }
        response=requests.get(band_data_url,params=data,headers=headers)
        r_json = response.json()
        if "items" not in r_json:
            return rows
        
        for stress in r_json['items']:
            row = {
                "timestamp": int(stress['timestamp']) * 1000000, # Convert to nanos 
                "fields" : {
                    "minimum_stress_level" : int(stress['minStress']),
                    "max_stress_level" : int(stress['maxStress']),
                    "mean_stress_level" : int(stress['avgStress']),
                    "relaxed_time_perc" : int(stress['relaxProportion']),
                    "normal_stress_time_perc" : int(stress['normalProportion']),
                    "medium_stress_time_perc" : int(stress['mediumProportion']),
                    "high_stress_time_perc" : int(stress['highProportion'])
                    },
                "tags" : {
                    "stress" : "daily"
                    }
            }           
            rows.append(row)
            
            # See whether we've been provided regular reads
            if "data" in stress:
                stress_dump = json.loads(stress['data'])
                for stresspoint in stress_dump:
                    row = {
                        "timestamp": int(stresspoint['time']) * 1000000, # Convert to nanos 
                        "fields" : {
                            "current_stress_level" : int(stresspoint['value'])
                            },
                        "tags" : {
                            "stress" : "point_in_time"
                            }
                    }           
                    rows.append(row)                

        return rows, None
