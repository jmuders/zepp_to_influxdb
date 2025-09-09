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

@dataclass
class ThresholdConfiguration:
    rapid_increase_threshold: float = 20.0  # bpm per sample
    elevation_multiplier: float = 1.3       # 30% above baseline
    sustained_elevation_threshold: float = 1.2  # 20% above baseline
    sustained_elevation_duration: int = 60      # seconds
    pattern_window_size: int = 10
    pattern_bpm_delta: float = 40.0

thresholds = ThresholdConfiguration()

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

    shr_extractor = SecondHeartRateExtractor(auth_info, query_duration=2)
    hr_data = shr_extractor.extract()

    loader = InfluxDbLoader(config)
    #loader.delete_all_data()
    loader.write_results(hr_data, "test-serial")