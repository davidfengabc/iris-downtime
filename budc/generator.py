# make decisions to generate new alert, or update previous alert
# generate a new alert if:
# new station with downtime
# old station worsens after x amount of time

import json
import datetime
from os import times
import pickle

# self.alert = {
#             'regressing':{
#                 ('NET', 'STATION') : {
#                     'current_downtime' : 5,
#                     'previous_downtime' : 2,
#                 }
#             }, 
#             'improving':{
#                 ('NET', 'STATION') : {
#                     'current_downtime' : 2,
#                     'previous_downtime' : 3,
#                 }
#             }
#         }

class Generator():
    # downtime_dict - pass in dictionary of station tuples as keys, downtime as values 
    # e.g. {('UO', 'ALSE'): 1, ('UW', 'LCCR'): 7}
    # elapsed_threshold in minutes
    def __init__(self, downtime_dict, downtime_threshold=3, elapsed_threshold=30):
        self.downtime_threshold = downtime_threshold
        self.elapsed_threshold = elapsed_threshold
        self.downtime_dict = downtime_dict
        self.previous_alert = None

        self.alert = Alert()
        

    
    def save_alert(self, alert_id, ofile = 'last_status.pickle'):
        self.alert.set_alert_id(alert_id)
        pickle.dump(self.alert, open(ofile, 'wb'))

    def retrieve_previous_alert(self, ifile = 'last_status.pickle'):
        try:
            self.previous_alert = pickle.load(open(ifile,'rb'))
        except FileNotFoundError as e:
            self.previous_alert = {}

    # decider - return 0 for no alert, 1 for update previous, and 2 for generate new alert
    def decider(self):
        alert_status = 0
        now = datetime.datetime.now()
        # self.alert = None

        if self.previous_alert is None:
            self.retrieve_previous_alert()

        

        if self.previous_alert == {}:
            for station, current_downtime in self.downtime_dict.items():

                if current_downtime >= self.downtime_threshold:
                    # generate alert
                    alert_status = 2
                if current_downtime > 0:
                    self.alert.add_station(station, None, current_downtime, 2)
        else:
            # previous alert exists, compare downtimes

            # first update stations from previous alert
            previous_stations = self.previous_alert.get_station_dict()
            
            # iterate through previously alerted stations
            for station, previous_stn_dict in previous_stations.items():
                previous_downtime = previous_stn_dict.get('current_downtime', -1)
                current_downtime = self.downtime_dict.get(station, -1)
                time_threshold = self.previous_alert.get_timestamp() + datetime.timedelta(minutes=self.elapsed_threshold)
                if station in self.downtime_dict:
                    delta = 0
                    if previous_downtime < current_downtime:
                        # regression
                        delta = 2
                        if (current_downtime > self.downtime_threshold):
                            alert_status = 2
                        else:
                            alert_status = (1 if alert_status < 2 else 2)
                    elif previous_downtime > current_downtime:
                        # improvement
                        delta = 1
                        alert_status = (1 if alert_status < 2 else 2)
                    else:
                        # same
                        #delta = self.previous_alert.get_delta(station)
                        delta = 0
                        alert_status = (1 if alert_status < 2 else 2)
                    self.alert.add_station(station, previous_downtime, current_downtime, delta)
                else:
                    # station doesn't exist in current dict - might happen if station was removed from configuration
                    # don't add to new alert
                    # self.alert.add_station(station, previous_downtime, -1, 0)
                    # alert_status = (1 if alert_status < 2 else 2)
                    pass

            # iterate through all current stations
            for station, current_downtime in self.downtime_dict.items():
                if station in previous_stations:
                    # should already be captured in the loop above
                    pass
                elif current_downtime == 0:
                    # don't care about good stations that don't exist in previous alert
                    continue
                elif current_downtime >= self.downtime_threshold:
                    # new station above threshold
                    self.alert.add_station(station, 0, current_downtime, 2)
                    alert_status = 2
                else:
                    # new station, downtime is not 0, but under threshold, don't report
                    pass
        
        if alert_status == 2:
            self.alert.set_timestamp(now)
        else:
            self.alert.set_timestamp(self.get_previous_timestamp())
        
        self.alert.set_update_time(now)

        return alert_status

    def get_alert(self):
        return self.alert

    def get_previous_alert_id(self):
        if self.previous_alert is None:
            self.retrieve_previous_alert()
        return self.previous_alert.get_alert_id()

    def get_previous_timestamp(self):
        if self.previous_alert is None:
            self.retrieve_previous_alert()
        return self.previous_alert.get_timestamp()


class Alert():
    def __init__(self):
        self.station_dict = {}
        self.timestamp = None
        self.update_time = None
        self.alert_id = None

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp
    
    def get_timestamp(self):
        return self.timestamp

    def set_update_time(self, timestamp):
        self.update_time = timestamp
    
    def get_update_time(self):
        return self.update_time

    def set_alert_id(self, alert_id):
        self.alert_id = alert_id

    def get_alert_id(self):
        return self.alert_id

    def add_station(self, station:tuple, previous_downtime: int, current_downtime: int, delta):
        self.station_dict[station] = {
            'previous_downtime' : previous_downtime,
            'current_downtime' : current_downtime,
            'delta' : delta
        }

    
    def get_delta(self, station):
        return self.station_dict[station]['delta']

    def get_station_dict(self):
        return self.station_dict


    def get_previous_downtime(self, station:tuple):
        return self.station_dict[station]['previous_downtime']


    def get_current_downtime(self, station:tuple):
        return self.station_dict[station]['current_downtime']

    def __str__(self) -> str:
        print_me = ''
        for station, downtime in self.station_dict.items():
            print_me += f'{station[1]}, {downtime}\n'

        print_me +=f'id: {self.alert_id}\ntimestamp: {self.timestamp}'
        return print_me

