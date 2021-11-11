# use os environment variables for:
# slack channel IRIS_DOWNTIME_CHANNEL
# token IRIS_DOWNTIME_TOKEN

import json
import datetime

import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import budc.generator as generator
import budc.budc as budc


class SlackInterface():
    def __init__(self, generator:generator.Generator, legend:dict, slack_channel, slack_token):
        self.reg_stns = []
        self.imp_stns = []
        self.constant_stns = []

        self.blocks = None

        self.client = None
        #self.logger = None
        

        self.generator = generator
        self.alert = generator.get_alert()
        
        self.legend = legend
        self.legend = self.markdown_clean(self.legend)
        

        self.slack_channel = slack_channel
        self.slack_token = slack_token

        self.connect_to_slack()

        self.slack_channel_id = self.get_channel_id()
 

    def connect_to_slack(self):
        self.client = WebClient(token=self.slack_token)
        #self.logger = logging.getLogger(__name__)
    
    def get_channel_id(self):
        for result in self.client.conversations_list():
            for channel in result['channels']:
                if channel["name"] == self.slack_channel:
                    return channel["id"]

    def add_regressing_station(self, station, current_downtime, previous_downtime):
        self.reg_stns.append((station, current_downtime, previous_downtime))

    def add_improving_station(self, station, current_downtime, previous_downtime):
        self.imp_stns.append((station, current_downtime, previous_downtime))

    def add_constant_station(self, station, current_downtime):
        self.constant_stns.append((station, current_downtime))

    def update_alert(self, ts):
        self.connect_generator()
        self.generate_msg(self.alert.get_timestamp(), self.alert.get_update_time())
        result = self.client.chat_update(
            channel=self.slack_channel_id,
            ts = ts,
            blocks=self.blocks
        )
        return result['ok'], result['ts']

    def new_alert(self):
        self.connect_generator()
        self.generate_msg(self.alert.get_timestamp(), self.alert.get_update_time())
        result = self.client.chat_postMessage(
            channel=self.slack_channel_id,
            blocks=self.blocks
        )

        return result['ok'], result['ts']

    def generate_msg(self, timestamp:datetime, update_time:datetime):
        slack_msg = {"blocks": []}

        time_blk = {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": f"Original alert time:  {timestamp}\nUpdate time: {update_time}"
            }
        }

        slack_msg["blocks"].append(time_blk)
        
        # regressing stations dictionary
        if len(self.reg_stns) > 0:
            text = ''
            for station, current_downtime, previous_downtime in self.reg_stns:
                if current_downtime != previous_downtime:
                    text += f'{station}\t~{self.legend.get(previous_downtime, "unk")}~ {self.legend.get(current_downtime, "unk")}\n'
                else:
                    text += f'{station}\t{self.legend.get(current_downtime, "unk")}\n'

            reg_blk = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Regressing Stations*\n{text.rstrip()}"
                }
            }

            slack_msg["blocks"].append(reg_blk)

        # improving stations dictionary
        if len(self.imp_stns) > 0:
            text = ''
            for station, current_downtime, previous_downtime in self.imp_stns:
                if current_downtime != previous_downtime:
                    text += f'{station}\t~{self.legend.get(previous_downtime, "unk")}~ {self.legend.get(current_downtime, "unk")}\n'
                else:
                    text += f'{station}\t{self.legend.get(current_downtime, "unk")}\n'

            imp_blk = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Improving Stations*\n{text.rstrip()}"
                }
            }

            slack_msg["blocks"].append(imp_blk)

        if len(self.constant_stns) > 0:
            text = ''
            for station, current_downtime in self.constant_stns:
                text += f'{station}\t{self.legend.get(current_downtime, "unk")}\n'

            const_blk = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Constants Stations*\n{text.rstrip()}"
                }
            }

            slack_msg["blocks"].append(const_blk)

        # timestamp block

        

        print(slack_msg)

        self.blocks = json.dumps(slack_msg["blocks"])

    def connect_generator(self):
        for station in self.alert.get_station_dict():
            delta = self.alert.get_delta(station)
            current_downtime = self.alert.get_current_downtime(station)
            previous_downtime = self.alert.get_previous_downtime(station)
            if delta == 1:
                # improving
                self.add_improving_station(station, current_downtime, previous_downtime)
            elif delta == 2:
                self.add_regressing_station(station, current_downtime, previous_downtime)
            else:
                self.add_constant_station(station, current_downtime)

    def markdown_clean(self, legend):
        legend_new = legend
        for level, text in legend.items():
            if text[0] == '>':
                legend_new[level] = f'&gt;{text[1:]}'

        return legend_new

if __name__ == "__main__":
    interface = SlackInterface()

    interface.add_regressing_station('blah', '10')
    interface.add_regressing_station('blah2', '0')
    interface.add_improving_station('blah3', '2')
    interface.add_improving_station('blah4', '1234')

    interface.generate_msg(datetime.datetime.now())
    print(interface.blocks)
    interface.new_alert()