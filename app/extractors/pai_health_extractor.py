import datetime
import requests

class PaiHealthExtractor:

    def __init__(self, auth_info, query_duration):
        self.auth_info = auth_info
        self.query_duration = query_duration

    def extract(self):
        ''' Retrieve Personal Actitivity Intelligence scoring data
        
        TODO: This could definitely be DRYer
        '''
        rows = []
        
        ''' calculate the times that the api query should check between
        '''
        today = datetime.datetime.today()
        today_end = datetime.datetime.combine(today, datetime.datetime.max.time()) 
        
        query_start_d = today - datetime.timedelta(days=self.query_duration)
        # Make it midnight  - the api doesn't seem to like mid-day queries
        query_start = datetime.datetime.combine(query_start_d, datetime.datetime.min.time())
        
        
        print("Retrieving PAI data")
        band_data_url=f"https://api-mifit-de2.zepp.com/users/{self.auth_info['token_info']['user_id']}/events"
        headers={
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        data={
            "limit" : 1000,
            "from" : query_start.strftime('%s000'),
            "to" : today_end.strftime('%s000'),
            "eventType" : "PaiHealthInfo",
            "timeZone" : "Europe/London"
        }   
        
        response=requests.get(band_data_url,params=data,headers=headers)
        r_json = response.json()
        if "items" not in r_json:
            return rows
        
        # Iterate through the daily entries
        for item in r_json['items']:
            timestamp_ms = int(item['timestamp'])

            # Heart rates       
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "heart_rate" : int(item['maxHr']),
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "hr_measure" : "PAI",
                        "hr_state" : "max"
                        }
                }        
            rows.append(row)
            
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "heart_rate" : int(item['restHr']),
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "hr_measure" : "PAI",
                        "hr_state" : "resting"
                        }
                }        
            rows.append(row)        
            
            
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "activity_duration_m" : int(item['lowZoneMinutes']),
                        "pai_score_bound" : int(item['lowZoneLowerLimit']),
                        "pai_score" : float(item['lowZonePai'])
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "PAI_bound" : "low"
                        }
                }
            rows.append(row)      
            
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "activity_duration_m" : int(item['mediumZoneMinutes']),
                        "pai_score_bound" : int(item['mediumZoneLowerLimit']),
                        "pai_score" : float(item['mediumZonePai'])
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "PAI_bound" : "medium"
                        }
                }
            rows.append(row)        
            
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "activity_duration_m" : int(item['highZoneMinutes']),
                        "pai_score_bound" : int(item['highZoneLowerLimit']),
                        "pai_score" : float(item['highZonePai'])
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "PAI_bound" : "high"
                        }
                }
            rows.append(row)          
                    
            row = {
                    "timestamp": timestamp_ms * 1000000, # Convert to nanos
                    "fields" : {
                        "scorable_activities" : len(item['activityScores']),
                        "pai_score" : float(item['dailyPai']),
                        "total_pai" : float(item['totalPai'])
                        },
                    "tags" : {
                        "PAI_measure" : "daily",
                        "PAI_bound" : "daily"
                        }
                }
            rows.append(row)            
        
        return rows, None