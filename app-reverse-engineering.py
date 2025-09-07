import base64
import json
import os
import requests
from app.mifit_to_influxdb import mifit_auth_email

def test_history_json_endpoint_1(auth_info):
    # # curl 'https://api-mifit-de2.zepp.com/v1/sport/run/history.json?r=5ABB54F5-2889-40D7-B4B7-C5498AB84A3B&count=20&need_sub_data=1&trackid=1757272913&type=&userid=7083497432' \
    # -H 'Host: api-mifit-de2.zepp.com' \
    # -H 'lang: de_DE' \
    # -H 'User-Agent: Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)' \
    # -H 'country: DE' \
    # -H 'appplatform: ios_phone' \
    # -H 'X-Hm-Ekv: 1' \
    # -H 'vn: 9.12.3' \
    # -H 'channel: appstore' \
    # -H 'hm-privacy-ceip: false' \
    # -H 'v: 2.0' \
    # -H 'appname: com.huami.midong' \
    # -H 'Connection: keep-alive' \
    # -H 'Accept-Language: de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8' \
    # -H 'cv: 1608_9.12.3' \
    # -H 'timezone: Europe/Berlin' \
    # -H 'vb: 202509051428' \
    # -H 'hm-privacy-diagnostics: false' \
    # -H 'apptoken: DQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAA4F588sfBFmgn7eKFphVJMu4f6iK57bmXWVm7GT2ct7OGU1TaEhJB011zi2TFW1AXAMiMlzaT390kia0Um_u-Q81SYazO_C_ojHSErVO8ZUxr9Ab8yb8cR5ZfClu8l_yaDQej7GE5FACRbqJ_X6MmkKR6t_gVmMaPd9LBz64hSaSpbEjeVdpOe9WwIxQOIces' \
    # -H 'X-Request-Id: 3D9EE788-2FF7-4BA3-8733-986CD841163A' \
    # -H 'Accept: */*' 
    # implement the curl command above in python requests
    url = 'https://api-mifit-de2.zepp.com/v1/sport/run/history.json'
    headers = {
        'Host': 'api-mifit-de2.zepp.com',
        'lang': 'de_DE',
        'User-Agent': 'Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)',
        'country': 'DE',
        'appplatform': 'ios_phone',
        #'X-Hm-Ekv': '1',
        'vn': '9.12.3',
        'channel': 'appstore',
        'hm-privacy-ceip': 'false',
        'v': '2.0',
        'appname': 'com.huami.midong',
        'Connection': 'keep-alive',
        'Accept-Language': 'de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8',
        'cv': '1608_9.12.3',
        'timezone': 'Europe/Berlin',
        'vb': '202509051428',
        'hm-privacy-diagnostics': 'false',
        'apptoken': auth_info['token_info']['app_token'],
        'X-Request-Id': '3D9EE788-2FF7-4BA3-8733-986CD841163A',
        'Accept': '*/*'
    }
    params = {
        'r': '5ABB54F5-2889-40D7-B4B7-C5498AB84A3B',
        'count': '20',
        'need_sub_data': '1',
        'trackid': '1757272913',
        'type': '',
        'userid': '7083497432'
    }
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code)
    print(response.json())

def test_history_json_endpoint_2(auth_info):
    #    curl 'https://api-mifit-de2.zepp.com/v1/sport/run/history.json?r=5ABB54F5-2889-40D7-B4B7-C5498AB84A3B&need_sub_data=1&startTrackId=1757196000&stopTrackId=1757196000&type=&userid=7083497432' \
    #-H 'Host: api-mifit-de2.zepp.com' \
    #-H 'lang: de_DE' \
    #-H 'User-Agent: Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)' \
    #-H 'country: DE' \
    #-H 'appplatform: ios_phone' \
    #-H 'X-Hm-Ekv: 1' \
    #-H 'vn: 9.12.3' \
    #-H 'channel: appstore' \
    #-H 'hm-privacy-ceip: true' \
    #-H 'v: 2.0' \
    #-H 'appname: com.huami.midong' \
    #-H 'Connection: keep-alive' \
    #-H 'Accept-Language: de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8' \
    #-H 'cv: 1608_9.12.3' \
    #-H 'timezone: Europe/Berlin' \
    #-H 'vb: 202509051428' \
    #-H 'hm-privacy-diagnostics: false' \
    #-H 'apptoken: DQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAA4F588sfBFmgn7eKFphVJMu4f6iK57bmXWVm7GT2ct7OGU1TaEhJB011zi2TFW1AXAMiMlzaT390kia0Um_u-Q81SYazO_C_ojHSErVO8ZUxr9Ab8yb8cR5ZfClu8l_yaDQej7GE5FACRbqJ_X6MmkKR6t_gVmMaPd9LBz64hSaSpbEjeVdpOe9WwIxQOIces' \
    #-H 'X-Request-Id: 103116AD-985D-4CF1-8A7F-BCD1D8FA3E24' \
    #-H 'Accept: */*' 
    url = 'https://api-mifit-de2.zepp.com/v1/sport/run/history.json'
    headers = {
        'Host': 'api-mifit-de2.zepp.com',
        'lang': 'de_DE',
        'User-Agent': 'Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)',
        'country': 'DE',
        'appplatform': 'ios_phone',
        #'X-Hm-Ekv': '1',
        'vn': '9.12.3',
        'channel': 'appstore',
        'hm-privacy-ceip': 'true',
        'v': '2.0',
        'appname': 'com.huami.midong',
        'Connection': 'keep-alive',
        'Accept-Language': 'de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8',
        'cv': '1608_9.12.3',
        'timezone': 'Europe/Berlin',
        'vb': '202509051428',
        'hm-privacy-diagnostics': 'false',
        'apptoken': auth_info['token_info']['app_token'],
        'X-Request-Id': '103116AD-985D-4CF1-8A7F-BCD1D8FA3E24',
        'Accept': '*/*'
    }
    params = {
        'r': '5ABB54F5-2889-40D7-B4B7-C5498AB84A3B',
        'need_sub_data': '1',
        'startTrackId': '1757196000',
        'stopTrackId': '1757196000',
        'type': '',
        'userid': '7083497432'
    } 
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code)
    print(response.json())

def file_info_event_second_heart_rate(auth_info):
    #    curl 'https://api-mifit-de2.zepp.com/users/me/fileInfo/events?r=5ABB54F5-2889-40D7-B4B7-C5498AB84A3B&eventType=second_heart_rate&from=1757203200000&limit=200&subType=real_data&to=1757274989000' \
    #-H 'Host: api-mifit-de2.zepp.com' \
    #-H 'User-Agent: Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)' \
    #-H 'appplatform: ios_phone' \
    #-H 'country: DE' \
    #-H 'lang: de_DE' \
    #-H 'vn: 9.12.3' \
    #-H 'channel: appstore' \
    #-H 'hm-privacy-ceip: false' \
    #-H 'v: 2.0' \
    #-H 'Connection: keep-alive' \
    #-H 'appname: com.huami.midong' \
    #-H 'Accept-Language: de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8' \
    #-H 'cv: 1608_9.12.3' \
    #-H 'timezone: Europe/Berlin' \
    #-H 'vb: 202509051428' \
    #-H 'hm-privacy-diagnostics: false' \
    #-H 'apptoken: DQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAAugo2NFuUz_Qj0HxzcMkfndEcYWBdQC7Ecsj8cfZM1TElfwBSUXQ7_lK7PqIq6Y-uzAoKNWV9PQYalCbiaaryxlKiy-IjAhbmuwblcrKUWKcl8g7FLD_s1-LwPKHipsRQu9ky_NlHqk99MnVr8by4svLY2QKT78g_5gz94P0iS4QN4GYk1QpEmFIrTlElh94k' \
    #-H 'X-Request-Id: 334B6DAF-7F8F-4F3E-B16E-383BBF9D26D3' \
    #-H 'Accept: */*'
    url = 'https://api-mifit-de2.zepp.com/users/me/fileInfo/events'
    headers = {
        #'Host': 'api-mifit-de2.zepp.com',
        #'User-Agent': 'Zepp/9.12.3 (iPhone; iOS 18.5; Scale/3.00)',
        #'appplatform': 'ios_phone',
        #'country': 'DE',
        #'lang': 'de_DE',
        #'vn': '9.12.3',
        #'channel': 'appstore',
        #'hm-privacy-ceip': 'false',
        #'v': '2.0',
        #'Connection': 'keep-alive',
        #'appname': 'com.huami.midong',
        #'Accept-Language': 'de-DE;q=1, en-DE;q=0.9, pt-PT;q=0.8',
        #'cv': '1608_9.12.3',
        #'timezone': 'Europe/Berlin',
        #'vb': '202509051428',
        #'hm-privacy-diagnostics': 'false',
        'apptoken': auth_info['token_info']['app_token'],
        #'X-Request-Id': '334B6DAF-7F8F-4F3E-B16E-383BBF9D26D3',
        #'Accept': '*/*'
    }
    params = {
        'r': '5ABB54F5-2889-40D7-B4B7-C5498AB84A3B',
        'eventType': 'second_heart_rate',
        'from': '1757203200000', # Sun Sep 07 2025 00:00:00 GMT+0000
        'limit': '200',
        'subType': 'real_data',
        'to': '1757282399000', # '1757274989000' # Sun Sep 07 2025 19:56:29 GMT+0000
    }
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code)

    # format json response nicely
    print(json.dumps(response.json(), indent=4))
    return response.json()

def get_second_heart_rate(auth_info):
    #    curl 'https://api-mifit-de2.zepp.com/files/SEC_HR/users/7083497432/queryDownUrlList?fileIds=5013157117' \
    #-H 'Host: api-mifit-de2.zepp.com' \
    #-H 'User-Agent: Zepp/9.12.3 (com.huami.watch; build:202509051428; iOS 18.5.0) Alamofire/5.9.0' \
    #-H 'appplatform: ios_phone' \
    #-H 'country: DE' \
    #-H 'lang: de_DE' \
    #-H 'vn: 9.12.3' \
    #-H 'channel: appstore' \
    #-H 'hm-privacy-ceip: false' \
    #-H 'v: 2.0' \
    #-H 'Connection: keep-alive' \
    #-H 'appname: com.huami.midong' \
    #-H 'Accept-Language: de-DE;q=1.0, en-DE;q=0.9, pt-PT;q=0.8' \
    #-H 'cv: 1608_9.12.3' \
    #-H 'timezone: Europe/Berlin' \
    #-H 'vb: 202509051428' \
    #-H 'hm-privacy-diagnostics: false' \
    #-H 'apptoken: DQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAA4F588sfBFmgn7eKFphVJMu4f6iK57bmXWVm7GT2ct7OGU1TaEhJB011zi2TFW1AXAMiMlzaT390kia0Um_u-Q81SYazO_C_ojHSErVO8ZUxr9Ab8yb8cR5ZfClu8l_yaDQej7GE5FACRbqJ_X6MmkKR6t_gVmMaPd9LBz64hSaSpbEjeVdpOe9WwIxQOIces' \
    #-H 'X-Request-Id: 369319CE-F061-4388-AC73-16CC0F939A00' \
    #-H 'Accept: */*' 
    url = 'https://api-mifit-de2.zepp.com/files/SEC_HR/users/7083497432/queryDownUrlList'
    headers = {
        'Host': 'api-mifit-de2.zepp.com',
        'User-Agent': 'Zepp/9.12.3 (com.huami.watch; build:202509051428; iOS 18.5.0) Alamofire/5.9.0',
        'appplatform': 'ios_phone',
        'country': 'DE',
        'lang': 'de_DE',
        'vn': '9.12.3',
        'channel': 'appstore',
        'hm-privacy-ceip': 'false',
        'v': '2.0',
        'Connection': 'keep-alive',
        'appname': 'com.huami.midong',
        'Accept-Language': 'de-DE;q=1.0, en-DE;q=0.9, pt-PT;q=0.8',
        'cv': '1608_9.12.3',
        'timezone': 'Europe/Berlin',
        'vb': '202509051428',
        'hm-privacy-diagnostics': 'false',
        'apptoken': auth_info['token_info']['app_token'],
        'X-Request-Id': '369319CE-F061-4388-AC73-16CC0F939A00',
        'Accept': '*/*'
    }
    params = {
        'fileIds': '5013157117',
    }
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code)
    print(response.json())

    download_url = response.json()['5013157117']
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
                    with open(name, 'wb') as f:
                        f.write(file_content)
                    try:
                        import second_heart_rate_pb2
                        hr_proto = second_heart_rate_pb2.SecondHeartRate()
                        hr_proto.ParseFromString(file_content)
                        print(hr_proto.section)
                        print(hr_proto)
                    except Exception as e:
                        print("Could not parse as protobuf:", e)
                    # As fallback, print the first 100 bytes as hex
                    print("First 100 bytes (hex):", file_content[:100].hex())



if __name__== "__main__":
     # Collect config
    config = {}
     # Get the Zepp credentials
    config['ZEPP_EMAIL'] = os.getenv("ZEPP_EMAIL", False)
    config['ZEPP_PASS'] = os.getenv("ZEPP_PASS", False)
    auth_info=mifit_auth_email(config['ZEPP_EMAIL'], config['ZEPP_PASS'])

    #test_history_json_endpoint_1(auth_info)
    #test_history_json_endpoint_2(auth_info)
    file_info_event_second_heart_rate(auth_info)
    get_second_heart_rate(auth_info)