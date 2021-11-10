import json
import datetime
import requests
import re

station_query = 'http://service.iris.edu/fdsnws/station/1/query?net=%s&starttime=%sT00:00:00&level=station&format=text&includecomments=true&nodata=404'


config = {
    'bud-report': 
        {
            'networks':
                {
                
                'UO': 
                    { 
                        'include':'*', 
                        #'exclude':'BUCK'
                    },
                
            
                'UW': 
                    {
                        'include':'*', 
                        #'exclude':'B,D'
                    }
                
                },
            'options':{}
        }
    }


class BudConfig():
    def __init__(self, configfile):
        self.configfile = configfile
        self.config = None
        self.stations = []
        with open(configfile, 'r') as fp:
            self.config = json.load(fp)

        self.parse_config()


    def parse_config(self):
        for network, values in self.config["bud-report"]["networks"].items():
            # if "include" is set to "*", then get all stations in network
            if re.search("\*", values["include"]):
                try:
                    values["include"] = self.get_stations_from_iris(network)
                except ValueError as e:
                    # network not found, go to next network
                    continue

            sta_in = [x.strip() for x in values["include"].split(',')]
            
            sta_ex = []
            if "exclude" in values:
                sta_ex = [x.strip() for x in values["exclude"].split(',')]

            for s in sta_in:
                if s not in sta_ex:
                    self.stations.append((network, s))


    def get_stations_from_iris(self, network):
        epoch_date = datetime.date.today() - datetime.timedelta(days=1)
        url = station_query %(network, epoch_date)
        #print(url)

        resp = requests.get(url)
        #print(resp.text)
        if resp.status_code != 200:
            raise ValueError("network not found")
        else:
            return(self.parse_fdsnws(resp.text))

    # return string of stations, separated by commas e.g.  "BUCK,HBO,ALSE"
    def parse_fdsnws(self, text):
        stations = []
        lines = text.split('\n')

        # toss header line
        lines = lines[1:]

        for line in lines:
            cells = line.split('|')

            # in case line is empty, discard
            if len(cells) > 1:
                stations.append(cells[1])

        eval = ','.join(stations)
        return eval


    # returns tuples of (network, station) e.g. [('UO', 'ALSE'), ('UO', 'BCAT')]
    def get_stations(self):
        return self.stations


if __name__ == "__main__":
    config_json = json.dumps(config, indent=4)

    with open('config.json','w') as file:
        file.write(config_json)
    
    
    bc = BudConfig('config.json')
