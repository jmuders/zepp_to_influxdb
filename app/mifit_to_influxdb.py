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

from episodes_detector import EpisodesDetector
from huami_extractor import HuamiExtractor
from influxdb_loader import InfluxDbLoader
from config_loader import load_config

# Load .env from project root
try:
    from load_env import *
except ImportError:
    pass

def main():
    ''' Main entry point
    '''
    config = load_config()    

    extractor = HuamiExtractor(config['ZEPP_EMAIL'], 
                               config['ZEPP_PASS'], 
                               config['QUERY_DURATION'])
    result = extractor.extract()
    
    loader = InfluxDbLoader(config)
    loader.write_results(result['data'], result['serial'])

    detector = EpisodesDetector(config)
    detector.detect()

if __name__== "__main__":
    main()
