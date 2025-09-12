
import base64
import datetime
import json
import requests

from tools.minute_utils import minute_to_timestamp

class BandDataExtractor:

    def __init__(self, auth_info, query_duration):
        self.auth_info = auth_info
        self.query_duration = query_duration

    def extract(self):
        ''' Retrieve information for the band/watch associated with the account
        '''
        result_set = []
        serial = "unknown"
        
        ''' We need to calculate today's midnight so that we can assess whether
        a date entry relates to today or not.
        
        The idea being that we want to write points throughout the current day
        but for previous days only want to write/update the previous entry
        
        The value of today will also be used to construct the query string presented
        to the api
        '''
        today = datetime.datetime.today()
        midnight = datetime.datetime.combine(today, datetime.datetime.min.time())
        today_ts = today.strftime('%s')    

        query_start = today - datetime.timedelta(days=self.query_duration)

        print("Retrieving mi band data")
        band_data_url='https://api-mifit.huami.com/v1/data/band_data.json'
        headers={
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        data={
            'query_type': 'detail',
            'device_type': 'android_phone',
            'userid': self.auth_info['token_info']['user_id'],
            'from_date': query_start.strftime('%Y-%m-%d'),
            'to_date': today.strftime('%Y-%m-%d'),
        }
        response=requests.get(band_data_url,params=data,headers=headers)
        
        for daydata in response.json()['data']:
            day = daydata['date_time']
            print(day)
            # Parse the date into a datetime
            day_ts = datetime.datetime.strptime(daydata['date_time'], '%Y-%m-%d')
            
            # If day_ts is < midnight we want to set the timestamp to be 23:59:59 
            # on that day. If not, then we use the current timestamp.
            if day_ts < midnight:
                ts = datetime.datetime.combine(day_ts, datetime.datetime.max.time()).strftime('%s')
            else:
                ts = today_ts
            
            if "data_hr" in daydata:
                print("Extracting heart rate")
                result_set = result_set + self.translate_heartrate_blob(daydata)
                
            summary=json.loads(base64.b64decode(daydata['summary']))
            for k,v in summary.items():
                if k=='stp':
                    # Extract step data
                    result_set = result_set + self.extract_step_data(ts, v, day)
                elif k=='slp':
                    # Extract the data
                    result_set = result_set + self.extract_sleep_data(ts, v, day)
                elif k == "goal":
                    result_set.append({
                        "timestamp": int(ts) * 1000000000, # Convert to nanos
                        "fields" : {
                            "step_goal" : int(v),
                            },
                        "tags" : {}
                    })
                elif k == "sn":
                    serial = v
                elif k == "sync":
                    result_set.append({
                        "timestamp": int(ts) * 1000000000, # Convert to nanos
                        "fields" : {
                            "last_sync" : int(v),
                            },
                        "tags" : {}
                    })                
                else:
                    print(f"Skipped {k} = {v}")
                 
        return result_set, serial

    @staticmethod
    def translate_heartrate_blob(daydata):
        ''' Extract the heart rate data blob from the JSON
        and convert to a list of stats
        '''
        
        # Create a datetime object from the date specified in JSON
        # this will be midnight.
        nowtime = datetime.datetime.strptime(daydata['date_time'], "%Y-%m-%d")
            
        number_blob = bytearray(base64.b64decode(daydata['data_hr']))
        #print(number_blob)
        adjusted_vals = []
        
        # Initialise values
        x = 1
        b=b''    
    
        # Iterate through the bytestring
        for byte_i in number_blob:
            # iterating over leads to us fetching ints
            # not bytes, so convert back
            byte = byte_i.to_bytes(length=1, byteorder="big")
            
            # Concatenate this byte onto the previous
            b += byte
            
            # Move the marker to the right
            x += 1
            
            # The data is a java short, so every
            # 2 bytes, convert it to an integer
            if x == 2:            
                # Convert the bytestring to an int
                v = int(b.hex(), 16)
                
                # Adjust the timestamp forward 1 minute
                nowtime = nowtime + datetime.timedelta(minutes=1)
                
                # They seem to use a high initialisation
                # value to indicate lack of data. If it's
                # higher than 200 skip it
                if v < 200:
                    # Append a point
                    adjusted_vals.append({
                            "timestamp": int(nowtime.strftime('%s')) * 1000000000, # Convert to nanos
                            "fields" : {
                                "heart_rate" : int(v),
                                },
                            "tags" : {
                                "hr_measure" : "periodic"
                                }
                        })
                    
                
                # Reset the byte string
                b = b''
                # Reset the counter
                x = 1

        return adjusted_vals
    
    @staticmethod
    def extract_sleep_data(ts, slp, day):
        ''' Extract sleep data and format it for feeding into InfluxDB
        '''
        rows = []
        row = {
            "timestamp": int(ts) * 1000000000, # Convert to nanos 
            "fields" : {
                "total_sleep_min" : slp['lt']+slp['dp'],
                "deep_sleep_min" : slp['dp'],
                "rem_sleep_min" : slp['lt'],
                "slept_from" : str(datetime.datetime.fromtimestamp(slp['st'])),
                "slept_to" : str(datetime.datetime.fromtimestamp(slp['ed'])),
                },
            "tags" : {
                "activity_type" : "sleep"
                }
        }
            
        rows.append(row)
        
        sleep_stages = 0
        stages_counters = {}
        # If there are stages recorded, also log those
        if 'stage' in slp:
            sleep_stages = len(slp['stage'])
            for sleep in slp['stage']:
                if sleep['mode'] == 4:
                    stage = 'light_sleep'
                elif sleep['mode'] == 5:
                    stage = 'deep_sleep'
                elif sleep['mode'] == 7:
                    stage = 'awake'                
                elif sleep['mode'] == 8:
                    stage = 'REM'                
                else:
                    stage = f"unknown_{sleep['mode']}"
                    
                start_epoch = minute_to_timestamp(sleep['start'], day)
                
                row = {
                    "timestamp": start_epoch * 1000000000, # Convert to nanos 
                    "fields" : {
                        "total_sleep_min" : sleep['stop'] - sleep['start']
                        },
                    "tags" : {
                        "activity_type" : "sleep_stage",
                        "sleep_type" : stage
                        }
                }           
                rows.append(row)

                # Create points for every minute in this state.
                stop_epoch = minute_to_timestamp(sleep['stop'], day)
                
                s = start_epoch
                while s <= stop_epoch:
                    row = {
                        "timestamp": s * 1000000000, # Convert to nanos 
                        "fields" : {
                            "current_sleep_state" : stage,
                            "current_sleep_state_int" : sleep['mode'],
                            },
                        "tags" : {
                            "activity_type" : "sleep_stage_tracker"
                            }
                    }           
                    rows.append(row)
                    s += 60
                
                # Increment the counter for the type
                # initialising if not already present
                if stage not in stages_counters:
                    stages_counters[stage] = 0
                stages_counters[stage] += 1
        
        
        # Record the number of sleep stages
        row = {
            "timestamp": int(ts) * 1000000000, # Convert to nanos 
            "fields" : {
                "recorded_sleep_stages" : sleep_stages
                },
            "tags" : {}
        }
            
        # Add a field for each of the recorded stages_counters 
        for stage in stages_counters:
            row['fields'][f"recorded_sleep_{stage}_events"] = stages_counters[stage]
            
        # Add the record
        rows.append(row)    
        
        return rows
        
    @staticmethod
    def extract_step_data(ts, stp, day):
        ''' Extract step data and return in a format ready for feeding
            into InfluxDB
        '''
        rows = []
        row = {
            "timestamp": int(ts) * 1000000000, # Convert to nanos 
            "fields" : {
                "total_steps" : stp['ttl'],
                "calories" : stp['cal'],            
                "distance_m" : stp['dis']
                },
            "tags" : {
                "activity_type" : "steps"
                }
        }
            
        rows.append(row)
        
        activity_count = 0
        activity_counters = {}
        # Iterate through any listed stages
        if "stage" in stp:
            activity_count = len(stp['stage'])        
            for activity in stp['stage']:
                if activity['mode'] == 1:
                    activity_type = 'slow_walking'
                elif activity['mode'] == 3:
                    activity_type = 'fast_walking'
                elif activity['mode'] == 4:
                    activity_type = 'running'
                elif activity['mode'] == 7:
                    activity_type = 'light_activity'
                else:
                    activity_type = f"unknown_{activity['mode']}"
                
                start_epoch = minute_to_timestamp(activity['start'], day)
                
                row = {
                    "timestamp": start_epoch * 1000000000, # Convert to nanos TODO 
                    "fields" : {
                        "total_steps" : activity['step'],
                        "calories" : activity['cal'],
                        "distance_m" : stp['dis'],
                        "activity_duration_m" : activity['stop'] - activity['start'],            
                        },
                    "tags" : {
                        "activity_type" : activity_type
                        }
                }
                rows.append(row)
                
                # Increment the type specific counter
                if activity_type not in activity_counters:
                    activity_counters[activity_type] = 0
                activity_counters[activity_type] += 1
                
                # Create an entry for each minute of this activity
                end_epoch = minute_to_timestamp(activity['stop'], day)
                s = start_epoch
                while s <= end_epoch:
                    row = {
                        "timestamp": s * 1000000000, # Convert to nanos 
                        "fields" : {
                            "current_activity_type" : activity_type,
                            "current_activity_type_int" : activity['mode'],
                            },
                        "tags" : {
                            "activity_type" : "activity_type_tracker"
                            }
                    }           
                    rows.append(row)
                    s += 60
                
        # Record the number of activities
        row = {
            "timestamp": int(ts) * 1000000000, # Convert to nanos 
            "fields" : {
                "recorded_activities" : activity_count
                },
            "tags" : {}
        }
        for activity in activity_counters:
            row['fields'][f"recorded_activity_{activity}_events"] = activity_counters[activity]
        rows.append(row)
        
        return rows
  

