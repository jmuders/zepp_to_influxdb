from influxdb_client import InfluxDBClient, Point

class InfluxDbLoader:
    ''' Class to handle loading data into InfluxDB
    '''
    def __init__(self, config):
        self.config = config

    def delete_all_data(self):
        ''' Delete all data in the specified bucket
        '''
        with InfluxDBClient(url=self.config['INFLUXDB_URL'], 
                            token=self.config['INFLUXDB_TOKEN'], 
                            org=self.config['INFLUXDB_ORG']) as client:
            delete_api = client.delete_api()
            start = "1970-01-01T00:00:00Z"
            stop = "2100-01-01T00:00:00Z"
            delete_api.delete(start, stop, f'_measurement="{self.config["INFLUXDB_MEASUREMENT"]}"', bucket=self.config['INFLUXDB_BUCKET'], org=self.config['INFLUXDB_ORG'])
            print(f"Deleted all data from bucket {self.config['INFLUXDB_BUCKET']}")
        
    def write_results(self, results, serial):
        ''' Open a connection to InfluxDB and write the results in
        '''
        with InfluxDBClient(url=self.config['INFLUXDB_URL'], 
                            token=self.config['INFLUXDB_TOKEN'], 
                            org=self.config['INFLUXDB_ORG']) as client:
            with client.write_api() as _write_client:
                points = []
                # setup progress bar for large uploads
                total = len(results)
                print(f"Writing {total} points to InfluxDB")
                for i, row in enumerate(results):
                    p = Point(self.config['INFLUXDB_MEASUREMENT'])
                    for tag in row['tags']:
                        p = p.tag(tag, row['tags'][tag])
                    p = p.tag("serial_num", serial)
                    for field in row['fields']:
                        p = p.field(field, row['fields'][field])
                    p = p.time(row['timestamp'])
                    points.append(p)
                    if (i + 1) % 5000 == 0 or (i + 1) == total:
                        print(f"Writing point {i + 1} of {total}")
                        _write_client.write(
                            self.config['INFLUXDB_BUCKET'],
                            self.config['INFLUXDB_ORG'],
                            points
                        )
                        points = []
                # Write all points in a single batch
                if points:
                    _write_client.write(
                        self.config['INFLUXDB_BUCKET'],
                        self.config['INFLUXDB_ORG'],
                        points
                    )