from dataclasses import dataclass
from influxdb_client import InfluxDBClient
import pandas as pd


@dataclass
class ThresholdConfiguration:
    rapid_increase_threshold: float = 20.0  # bpm per sample
    elevation_multiplier: float = 1.3       # 30% above baseline
    sustained_elevation_threshold: float = 1.2  # 20% above baseline
    sustained_elevation_duration: int = 60      # seconds
    pattern_window_size: int = 10
    pattern_bpm_delta: float = 40.0

class EpisodesDetector:

    def __init__(self, config):
        self.thresholds = ThresholdConfiguration()
        self.config = config

    def get_second_heart_rate_df(self) -> pd.DataFrame:
        with InfluxDBClient(url=self.config['INFLUXDB_URL'], 
                            token=self.config['INFLUXDB_TOKEN'], 
                            org=self.config['INFLUXDB_ORG']) as client:

            query = f'''
from(bucket: "{self.config["INFLUXDB_BUCKET"]}")
  |> range(start: -{self.config['QUERY_DURATION']}d)
  |> filter(fn: (r) => r._measurement == "{self.config["INFLUXDB_MEASUREMENT"]}")
  |> filter(fn: (r) => r._field == "heart_rate_secs")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "heart_rate_secs"])
  |> rename(columns: {{_time: "ts", heart_rate_secs: "hr"}})
'''
            df = client.query_api().query_data_frame(org=self.config['INFLUXDB_ORG'], query=query)
            df['ts'] = pd.to_datetime(df['ts'])
            print('Size of dataframe:', df.shape)

            return df

    def detect_seizures(self, df) -> pd.DataFrame:
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
        df["hrv_rapid_change"] = df["hrv"] > self.thresholds.rapid_increase_threshold

        # mark elevated heart rate
        df["hr_elevated"] = df["hr"] > (df["median_baseline"] * self.thresholds.elevation_multiplier)

        # Calculate elevated heart rate streaks with start and end times
        df["hr_sustained_elevated"] = df["hr"] > (df["median_baseline"] * self.thresholds.sustained_elevation_threshold)

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

        df['hr_pattern_window'] = df['hr'].rolling(window=self.thresholds.pattern_window_size, 
                                                   min_periods=self.thresholds.pattern_window_size, 
                                                   center=True).apply(lambda x: (x.max() - x.min()) > self.thresholds.pattern_bpm_delta, 
                                                                      raw=True).astype(bool)

        # compute confidence score in pandas
        df["confidence_score"] = (
            df["hrv_rapid_change"].astype(float) * 0.3 +
            df["hr_sustained_elevated"].astype(float) * 0.2 + 
            (df['hr_elevation_streaks'] > self.thresholds.sustained_elevation_duration).astype(float) * 0.2 + 
            df["hr_pattern_window"].astype(float) * 0.3
        )

        df['episode_detection'] = df['confidence_score'] >= 0.7

        return df

    def write_results_to_influx(self, df: pd.DataFrame):
        with InfluxDBClient(url=self.config['INFLUXDB_URL'], 
                            token=self.config['INFLUXDB_TOKEN'], 
                            org=self.config['INFLUXDB_ORG']) as client:

            with client.write_api() as write_api:
                # Prepare data for InfluxDB
                points = []
                total = len(df)
                for i, (_, row) in enumerate(df.iterrows()):
                    point = {
                        "measurement": "zepp_detection",
                        "time": row['ts'],
                        "fields": {
                            "hr": int(row['hr']),
                            "mean_baseline": float(row['mean_baseline']) if pd.notnull(row['mean_baseline']) else None,
                            "median_baseline": float(row['median_baseline']) if pd.notnull(row['median_baseline']) else None,
                            "hrv": float(row['hrv']) if pd.notnull(row['hrv']) else None,
                            "hrv_std": float(row['hrv_std']) if pd.notnull(row['hrv_std']) else None,
                            "rolling_mean": float(row['rolling_mean']) if pd.notnull(row['rolling_mean']) else None,
                            "rolling_std": float(row['rolling_std']) if pd.notnull(row['rolling_std']) else None,
                            "hrv_rapid_change": bool(row['hrv_rapid_change']),
                            "hr_elevated": bool(row['hr_elevated']),
                            "hr_sustained_elevated": bool(row['hr_sustained_elevated']),
                            "hr_elevation_streaks": int(row['hr_elevation_streaks']),
                            "hr_pattern_window": bool(row['hr_pattern_window']),
                            "confidence_score": float(row['confidence_score']) if pd.notnull(row['confidence_score']) else None,
                            "episode_detection": bool(row['episode_detection'])
                        }
                    }
                    points.append(point)
                    if (i + 1) % 5000 == 0 or (i + 1) == total:
                        print(f"Writing point {i + 1} of {total}")
                        write_api.write(
                            bucket=self.config['INFLUXDB_BUCKET'],
                            record=points
                        )
                        points = []
                # Write all points in a single batch
                if points:
                    write_api.write(
                        self.config['INFLUXDB_BUCKET'],
                        self.config['INFLUXDB_ORG'],
                        points
                    )

            # Write data to InfluxDB
            write_api.write(bucket=self.config['INFLUXDB_BUCKET'], record=points)

    def detect(self):
        df = self.get_second_heart_rate_df()

        # loop through the dataframe with a sliding window of 30 minutes and store the results in a new dataframe
        window_size = 30 * 60  # 30 minutes in seconds

        results = []
        for start in range(0, len(df), window_size):
            end = start + window_size
            window = df.iloc[start:end]
            self.detect_seizures(window)
            results.append(window)

        self.write_results_to_influx(pd.concat(results))

        return pd.concat(results)