import base64
from dataclasses import dataclass
import json
import os
import requests
import datetime
import pytz
from influxdb_loader import InfluxDbLoader
from huami_extractor import HuamiExtractor
from config_loader import load_config
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load .env from project root
try:
    from load_env import *
except ImportError:
    pass

@dataclass
class ThresholdConfiguration:
    rapid_increase_threshold: float = 20.0  # bpm per sample
    elevation_multiplier: float = 1.3       # 30% above baseline
    sustained_elevation_threshold: float = 1.2  # 20% above baseline
    sustained_elevation_duration: int = 60      # seconds
    pattern_window_size: int = 10
    pattern_bpm_delta: float = 40.0

thresholds = ThresholdConfiguration()

def file_info_event_second_heart_rate(auth_info, query_duration=1):

    # yesterday midnight timestamp in milliseconds in utc
    end = datetime.datetime.now(datetime.timezone.utc)
    end_ts = int(end.timestamp()) * 1000
    start = end - datetime.timedelta(days=query_duration)
    start_midnight = datetime.datetime.combine(start.date(), datetime.datetime.min.time(), tzinfo=datetime.timezone.utc)
    start_midnight_ts = int(start_midnight.timestamp()) * 1000
    end_second_before_midnight = datetime.datetime.combine(end.date(), datetime.datetime.max.time(), tzinfo=datetime.timezone.utc)
    end_ts = int(end_second_before_midnight.timestamp()) * 1000
    print("Start midnight timestamp (ms):", start_midnight_ts)
    print("End timestamp (ms):", end_ts)

    url = 'https://api-mifit-de2.zepp.com/users/me/fileInfo/events'
    headers = {
        'apptoken': auth_info['token_info']['app_token'],
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


def get_second_heart_rate(auth_info, fileIds):
    url = 'https://api-mifit-de2.zepp.com/files/SEC_HR/users/7083497432/queryDownUrlList'
    headers = {
        'apptoken': auth_info['token_info']['app_token'],
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
                            
                            hr_data = translate_second_heart_rate(hr_proto)
                            response_data = response_data + hr_data
                            
                        except Exception as e:
                            print("Could not parse as protobuf:", e)
                        
                        print("Finished processing file: ", name)
                
    return response_data

def translate_second_heart_rate(data):
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

def detect_seizures(df, thresholds: ThresholdConfiguration) -> pd.DataFrame:
    ''' Detect potential seizure episodes in the heart rate data
    '''
    # filter out noise from the heart rate data
    #df['hr'] = df['hr'].rolling(window=2, center=True).mean()

    window = 600
    min_periods = 5

    # compute based on heart rate
    df['mean_baseline'] = df['hr'].rolling(window=window, min_periods=min_periods, center=True).mean()
    df['median_baseline'] = df['hr'].rolling(window=window, min_periods=min_periods, center=True).median()

    # compute the heart rate variability (HRV)
    window = 10
    min_periods = 5

    df["hrv"] = df["hr"].diff().abs()
    df["hrv_std"] = df["hr"].rolling(window=window, min_periods=min_periods, center=True).std()

    # Rolling-Mean & Rolling-Std
    df["rolling_mean"] = df["hrv"].rolling(window=window, min_periods=min_periods, center=True).mean()
    df["rolling_std"] = df["hrv"].rolling(window=window, min_periods=min_periods, center=True).std()

    # mark rapid changes
    df["hrv_rapid_change"] = df["hrv"] > thresholds.rapid_increase_threshold

    # mark elevated heart rate
    df["hr_elevated"] = df["hr"] > (df["median_baseline"] * thresholds.elevation_multiplier)

    # Calculate elevated heart rate streaks with start and end times
    df["hr_sustained_elevated"] = df["hr"] > (df["median_baseline"] * thresholds.sustained_elevation_threshold)

    df['elevated_group'] = (df["hr_sustained_elevated"] != df["hr_sustained_elevated"].shift()).cumsum()
    elevated_streaks = df[df["hr_sustained_elevated"]].groupby('elevated_group').agg(
        start_idx=('ts', 'first'),
        end_idx=('ts', 'last'),
        streak_len=('ts', 'count')
    ).reset_index()

    # Mark streak intervals in the dataframe for plotting
    df['hr_elevation_streaks'] = 0
    for _, row in elevated_streaks.iterrows():
        mask = (df['ts'] >= row['start_idx']) & (df['ts'] <= row['end_idx'])
        df.loc[mask, 'hr_elevation_streaks'] = row['streak_len']

    df['hr_pattern_window'] = df['hr'].rolling(window=thresholds.pattern_window_size, min_periods=thresholds.pattern_window_size, center=True).apply(lambda x: (x.max() - x.min()) > thresholds.pattern_bpm_delta, raw=True).astype(bool)

    # compute confidence score in pandas
    df["confidence_score"] = (
        df["hrv_rapid_change"].astype(float) * 0.3 +
        df["hr_sustained_elevated"].astype(float) * 0.2 + 
        (df['hr_elevation_streaks'] > thresholds.sustained_elevation_duration).astype(float) * 0.2 + 
        df["hr_pattern_window"].astype(float) * 0.3
    )

    df['episode_detection'] = df['confidence_score'] >= 0.7

    return df

if __name__== "__main__":

    config = load_config()

    extractor = HuamiExtractor(config['ZEPP_EMAIL'], config['ZEPP_PASS'])
    auth_info = extractor.auth_info

    fileIds = file_info_event_second_heart_rate(auth_info, 2)
    hr_data = get_second_heart_rate(auth_info, fileIds)

    loader = InfluxDbLoader(config)
    #loader.delete_all_data()
    loader.write_results(hr_data, "test-serial")