import datetime
import json
import pytz
import requests

class SecondHeartRateExtractor:
    ''' Extractor for second heart rate data from Zepp API
    '''
    def __init__(self, auth_info, query_duration=1):
        self.auth_info = auth_info
        self.query_duration = query_duration

    def translate_second_heart_rate(self, data):
        ''' Translate the second heart rate protobuf data into a list of dicts
        '''
        # get timezone of Portugal
        timezone_pt = pytz.timezone('Europe/Lisbon')

        results = []
        for section in data.section:
            # timestamp from unix timestamp in seconds
            start_timestamp = datetime.datetime.fromtimestamp(section.start_timestamp, tz=timezone_pt)
            for i, hr in enumerate(section.heart_rate):
                # start time + i seconds
                timestamp = start_timestamp + datetime.timedelta(seconds=i)

                if hr < 200:
                    results.append({
                        'timestamp': int(timestamp.strftime('%s')) * 1000000000,
                        "fields" : {
                            "heart_rate_secs" : int(hr),
                        },
                        "tags" : {
                            "hr_measure" : "periodic"
                        }
                    })
        return results
    
    def get_second_heart_rate(self, fileIds):
        ''' Retrieve and parse second heart rate data files from the Zepp API
        '''
        url = 'https://api-mifit-de2.zepp.com/files/SEC_HR/users/7083497432/queryDownUrlList'
        headers = {
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        params = {
            'fileIds': fileIds,
        }
        response = requests.get(url, headers=headers, params=params)
        print(response.status_code)
        print(response.json())

        response_data = []
        for fileId in fileIds:
            download_url = response.json()[fileId]
            print("Download URL for heart rate data:", download_url)

            # download the file from the download_url
            file_response = requests.get(download_url)

            # use the file_response content as binary data without saving to disk
            if file_response.status_code == 200:
                print("Successfully downloaded heart rate data")
                # process the binary data as needed
                heart_rate_data = file_response.content
                print(f"Heart rate data size: {len(heart_rate_data)} bytes")

                # unzip the data if needed (assuming it's a ZIP file)
                import zipfile
                import io
                with zipfile.ZipFile(io.BytesIO(heart_rate_data)) as zf:
                    for name in zf.namelist():
                        print(f"Found file in zip: {name}")
                        with zf.open(name) as f:
                            file_content = f.read()
                            print(f"Extracted file size: {len(file_content)} bytes")

                            # write to a file or process as needed
                            #with open(name, 'wb') as f:
                            #    f.write(file_content)
                            try:
                                import second_heart_rate_pb2
                                hr_proto = second_heart_rate_pb2.SecondHeartRate()
                                hr_proto.ParseFromString(file_content)
                                #print(hr_proto.section)
                                
                                hr_data = self.translate_second_heart_rate(hr_proto)
                                response_data = response_data + hr_data
                                
                            except Exception as e:
                                print("Could not parse as protobuf:", e)
                            
                            print("Finished processing file: ", name)
                    
        return response_data
    
    def file_info_event_second_heart_rate(self):
        ''' Retrieve file info events for second heart rate data from the Zepp API
        '''
        # yesterday midnight timestamp in milliseconds in utc
        end = datetime.datetime.now(datetime.timezone.utc)
        end_ts = int(end.timestamp()) * 1000
        start = end - datetime.timedelta(days=self.query_duration)
        start_midnight = datetime.datetime.combine(start.date(), datetime.datetime.min.time(), tzinfo=datetime.timezone.utc)
        start_midnight_ts = int(start_midnight.timestamp()) * 1000
        end_second_before_midnight = datetime.datetime.combine(end.date(), datetime.datetime.max.time(), tzinfo=datetime.timezone.utc)
        end_ts = int(end_second_before_midnight.timestamp()) * 1000
        print("Start midnight timestamp (ms):", start_midnight_ts)
        print("End timestamp (ms):", end_ts)

        url = 'https://api-mifit-de2.zepp.com/users/me/fileInfo/events'
        headers = {
            'apptoken': self.auth_info['token_info']['app_token'],
        }
        params = {
            'r': '5ABB54F5-2889-40D7-B4B7-C5498AB84A3B',
            'eventType': 'second_heart_rate',
            'from': start_midnight_ts, # Sun Sep 07 2025 00:00:00 GMT+0000
            'limit': '200',
            'subType': 'real_data',
            'to': end_ts, # '1757274989000' # Sun Sep 07 2025 19:56:29 GMT+0000
        }
        response = requests.get(url, headers=headers, params=params)
        print(response.status_code)

        json_response = response.json()
        print(json.dumps(json_response, indent=4))

        fileIds = []
        for item in json_response['items']:
            print("Event timestamp:", item['timestamp'])
            for sample in item['value']['samples']:
                if sample['fileId'] not in fileIds:
                    fileIds.append(sample['fileId'])

        print("Found fileIds for second heart rate data:", fileIds)
        return fileIds


    def extract(self):

        fileIds = self.file_info_event_second_heart_rate()
        hr_data = self.get_second_heart_rate(fileIds)

        return hr_data

    