import datetime
import json
import requests

class BloodOxygenExtractor:
    def __init__(self, auth_info, query_duration):
        self.auth_info = auth_info
        self.query_duration = query_duration

    def extract(self):
        rows = []
        
        ''' calculate the times that the api query should check between
        '''
        today = datetime.datetime.today()
        today_end = datetime.datetime.combine(today, datetime.datetime.max.time()) 

        query_start_d = today - datetime.timedelta(days=self.query_duration)
        # Make it midnight  - the api doesn't seem to like mid-day queries
        query_start = datetime.datetime.combine(query_start_d, datetime.datetime.min.time())
        
        
        print("Retrieving blood oxygen data")
        band_data_url=f"https://api-mifit.zepp.com/users/{self.auth_info['token_info']['user_id']}/events"
        headers={
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        data={
            'from': query_start.strftime('%s000'),
            'to': today_end.strftime('%s000'),
            "eventType": "blood_oxygen",
            "limit": 1000,
            "timeZone" : "Europe/London"
        }
        response=requests.get(band_data_url,params=data,headers=headers)
        r_json = response.json()

        if "items" not in r_json:
            return rows
        
        for blood in r_json['items']:
            if blood['subType'] == "odi":
                rows.append(self.processODIEvent(blood))
            elif blood['subType'] == "osa_event":
                rows.append(self.processOSAEvent(blood))
            elif blood['subType'] == "click":
                rows.append(self.processBloodClickEvent(blood))

        return rows, None

    @staticmethod
    def processBloodClickEvent(record):
        ''' Process a "click" event
        
        This appears to be the user manually triggering a blood
        oxygen reading from the watch/band (utilities/zepp_to_influxdb#6)
        '''
        extra = json.loads(record['extra'])
        return {
            "timestamp": int(record['timestamp']) * 1000000, # Convert to nanos 
            "fields" : {
                "spo2_level" : float(extra['spo2']),
                },
            "tags" : {
                "blood_event" : "manual_read"
                }
        }   

    @staticmethod
    def processOSAEvent(record):
        ''' Process a possible Obstructive Sleep Apnea event
        '''
        
        osa_record = json.loads(record['extra'])
        
        return {
            "timestamp": int(record['timestamp']) * 1000000, # Convert to nanos 
            "fields" : {
                "spo2_decrease" : float(osa_record['spo2_decrease']),
                },
            "tags" : {
                "blood_event" : "osa"
                }
        }           

    @staticmethod    
    def processODIEvent(record):
        ''' Process an ODI event
        '''
        return {
            "timestamp": int(record['timestamp']) * 1000000, # Convert to nanos 
            "fields" : {
                "odi_read" : float(record['odi']),
                # Not sure what this is, skipping for now 
                # (I *think* it might just be a record ID)
                # "odi_number" : int(record['odiNum']),
                #
                # There are also "cost" and "valid"
                "score" : float(record['score']),
                },
            "tags" : {
                "blood_event" : "odi"
                }
        }       
