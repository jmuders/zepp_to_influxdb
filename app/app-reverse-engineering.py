from dataclasses import dataclass
from second_heart_rate_extractor import SecondHeartRateExtractor
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





if __name__== "__main__":

    config = load_config()

    extractor = HuamiExtractor(config['ZEPP_EMAIL'], config['ZEPP_PASS'])
    auth_info = extractor.auth_info

    shr_extractor = SecondHeartRateExtractor(auth_info, query_duration=2)
    hr_data = shr_extractor.extract()

    loader = InfluxDbLoader(config)
    #loader.delete_all_data()
    loader.write_results(hr_data, "test-serial")