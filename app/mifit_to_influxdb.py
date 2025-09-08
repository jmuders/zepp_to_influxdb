#!/usr/bin/env python3
#
#
# Mi-Fit API to InfluxDB
#
# Polls the Mi-Fit/Zepp API to retrieve smart-band information
# then writes stepcounts etc onwards to InfluxDB
#
# Credit for API comms approach goes to Michael Wyraz
# https://github.com/micw/hacking-mifit-api
#
# pip install influxdb-client
'''
Copyright (c) 2023 B Tasker, M Wyraz

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

    Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import os
import sys
from huami_extractor import HuamiExtractor
from influxdb_loader import InfluxDbLoader

# Load .env from project root
try:
    from load_env import *
except ImportError:
    pass


def load_config():
    ''' Load configuration from environment variables
    '''
    config = {}

    # InfluxDB settings
    config['INFLUXDB_URL'] = os.getenv("INFLUXDB_URL", False)
    config['INFLUXDB_TOKEN'] = os.getenv("INFLUXDB_TOKEN", "")
    config['INFLUXDB_ORG'] = os.getenv("INFLUXDB_ORG", "")
    config['INFLUXDB_MEASUREMENT'] = os.getenv("INFLUXDB_MEASUREMENT", "zepp")
    config['INFLUXDB_BUCKET'] = os.getenv("INFLUXDB_BUCKET", "zepp")

    # How many days data should we request from the API?
    config['QUERY_DURATION'] = int(os.getenv("QUERY_DURATION", 2))
    
    # Get the Zepp credentials
    config['ZEPP_EMAIL'] = os.getenv("ZEPP_EMAIL", False)
    config['ZEPP_PASS'] = os.getenv("ZEPP_PASS", False)

    if not config['ZEPP_EMAIL'] or not config['ZEPP_PASS']:
        print("Error: Credentials not provided")
        sys.exit(1)
    
    return config

def main():
    ''' Main entry point
    '''
    config = load_config()    

    extractor = HuamiExtractor(config['ZEPP_EMAIL'], 
                               config['ZEPP_PASS'], 
                               config['QUERY_DURATION'])

    try:
        result_set, serial = extractor.get_band_data()
    except:
        print("Failed to collect band data")

    try:
        stress_rows = extractor.get_stress_data()
        result_set = result_set + stress_rows
    except:
        print("Failed to collect stress data")
    
    try:
        blood_o2 = extractor.get_blood_oxygen_data()
        result_set = result_set + blood_o2
    except:
        print("Failed to collect blood oxygen data")
    
    try:
        pai = extractor.get_PAI_data()
        result_set = result_set + pai
    except:
        print("Failed to collect PAI information")
    
    # Write into InfluxDB
    loader = InfluxDbLoader(config)
    loader.write_results(result_set, serial)

if __name__== "__main__":
    main()
