
import os
import sys


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