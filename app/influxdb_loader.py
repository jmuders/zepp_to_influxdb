from influxdb_client import InfluxDBClient, Point

class InfluxDbLoader:
    ''' Class to handle loading data into InfluxDB
    '''
    def __init__(self, config):
        self.config = config

    def write_results(self, results, serial):
        ''' Open a connection to InfluxDB and write the results in
        '''
        with InfluxDBClient(url=self.config['INFLUXDB_URL'], 
                            token=self.config['INFLUXDB_TOKEN'], 
                            org=self.config['INFLUXDB_ORG']) as client:
            with client.write_api() as _write_client:
                # Iterate through the results generating and writing points
                for row in results:
                    p = Point(self.config['INFLUXDB_MEASUREMENT'])
                    for tag in row['tags']:
                        p = p.tag(tag, row['tags'][tag])
                    p = p.tag("serial_num", serial)
                    for field in row['fields']:
                        p = p.field(field, row['fields'][field])
                    p = p.time(row['timestamp'])

                    _write_client.write(self.config['INFLUXDB_BUCKET'], 
                                        self.config['INFLUXDB_ORG'], p)