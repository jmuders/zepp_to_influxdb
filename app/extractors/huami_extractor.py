import requests
import urllib
from tools.minute_utils import fail, minute_to_timestamp
from extractors.second_heart_rate_extractor import SecondHeartRateExtractor
from extractors.band_data_extractor import BandDataExtractor
from extractors.stress_data_extractor import StressDataExtractor
from extractors.pai_health_extractor import PaiHealthExtractor
from extractors.blood_oxygen_extractor import BloodOxygenExtractor

class HuamiExtractor:
    ''' Class to handle extraction of data from the Huami (Mi-Fit/Zepp) API
    '''
    def __init__(self, email, password, query_duration=2):
        self.email = email
        self.password = password
        self.query_duration = query_duration
        self.auth_info = self.mifit_auth_email()
        self.extractors = [
            BandDataExtractor(self.auth_info, query_duration),
            SecondHeartRateExtractor(self.auth_info, query_duration),
            StressDataExtractor(self.auth_info, query_duration),
            PaiHealthExtractor(self.auth_info, query_duration),
            BloodOxygenExtractor(self.auth_info, query_duration)
        ]

    def mifit_auth_email(self):
        ''' Log into the Mifit API using username and password
            in order to acquire an access token
        '''
        print("Logging in with email {}".format(self.email))
        auth_url='https://api-user.huami.com/registrations/{}/tokens'.format(urllib.parse.quote(self.email))
        data={
            'state': 'REDIRECTION',
            'client_id': 'HuaMi',
            'redirect_uri': 'https://s3-us-west-2.amazonws.com/hm-registration/successsignin.html',
            'token': 'access',
            'password': self.password,
        }
        response=requests.post(auth_url,data=data,allow_redirects=False)
        response.raise_for_status()
        redirect_url=urllib.parse.urlparse(response.headers.get('location'))
        response_args=urllib.parse.parse_qs(redirect_url.query)
        if ('access' not in response_args):
            fail('No access token in response')
        if ('country_code' not in response_args):
            fail('No country_code in response')

        print("Obtained access token")
        access_token=response_args['access'];
        country_code=response_args['country_code'];

        return self.mifit_login_with_token({
            'grant_type': 'access_token',
            'country_code': country_code,
            'code': access_token,
        })


    def mifit_login_with_token(self, login_data):
        ''' Log into the API using an access token
        
            This is the second stage of the login process
        '''
        login_url='https://account.huami.com/v2/client/login'
        data={
            'app_name': 'com.xiaomi.hm.health',
            'dn': 'account.huami.com,api-user.huami.com,api-watch.huami.com,api-analytics.huami.com,app-analytics.huami.com,api-mifit.huami.com',
            'device_id': '02:00:00:00:00:00',
            'device_model': 'android_phone',
            'app_version': '4.0.9',
            'allow_registration': 'false',
            'third_name': 'huami',
        }
        data.update(login_data)
        response=requests.post(login_url,data=data,allow_redirects=False)
        result=response.json()
        return result;

    def extract(self):
        result_set = []
        serial = "unknown"
        for extractor in self.extractors:
            try:
                res, sn = extractor.extract()
                result_set = result_set + res
                if sn is not None:
                    serial = sn
            except:
                print("Failed to collect extract data from ", extractor)

        
        try:
            blood_o2 = self.get_blood_oxygen_data()
            result_set = result_set + blood_o2
        except:
            print("Failed to collect blood oxygen data")
        
        
        return {
            'data': result_set,
            'serial': serial
        }

          
    