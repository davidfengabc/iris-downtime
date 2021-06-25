import requests
import re
import html
import datetime
from datetime import timezone
import json

from pathlib import Path
from bs4 import BeautifulSoup

slack_webhook = ""
slack_webhook_headers = {'Content-type': 'application/json'}
threshold = 2

downtime = [
    "< 1 min",      # 0
    "≥ 1 min",      # 1
    "> 10 min",     # 2
    "> 30 min",     # 3
    "> 1 hour",     # 4
    "> 2 hours",    # 5
    "> 6 hours",    # 6
    "> 1 day",      # 7
    "> 2 days",     # 8
    "> 3 days",     # 9
    "> 4 days",     # 10
    "> 5 days",     # 11
    "> 10 days"     # 12
            ]

# Legend from http://buddy.iris.washington.edu/bud_stuff/dmc/bud_monitor.PACNW.html
# FFFFFF < 1 min
# EBD6FF ≥ 1 min
# 9470BB > 10 min
# 3399FF > 30 min
# 00FF00 > 1 hour
# FFFF00 > 2 hours
# FF9966 > 6 hours
# FF3333 > 1 day
# FFB3B3 > 2 days
# CCCCCC > 3 days
# 999999 > 4 days
# 666666 > 5 days


class AlertFields:

    stn_field = {
            'type': 'mrkdwn',  # hardcode to markdown for now
            'text': None  # Station name
        }
    downtime_field = {
            'type': 'mrkdwn',  # hardcode to markdown for now
            'text': None  # downtime
        }
    alert_field = {
        'type': 'mrkdwn',  # hardcode to markdown for now
        'text': None  # downtime
    }


    def __init__(self, station, downtime):
        self.station = station
        self.downtime = downtime

    def get_stn_field(self):
        self.stn_field['text'] = self.station
        return self.stn_field

    def get_dt_field(self):
        self.downtime_field['text'] = self.downtime
        return self.downtime_field

    def get_alert_field(self):
        self.alert_field['text'] = f'{self.station} latency {self.downtime}'
        return self.alert_field


class SlackAlertPayload:

    blocks = {
        'blocks': [

        ]   # list of block_section
    }

    block_section = \
        {
                'type': 'section',
                'fields': []    # list of AlertFields
        }

    header_section = \
        {
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "header",
			}
		}

    first_alerts_section = \
        {
            'type': 'section',
            'fields': []  # list of AlertFields
        }

    regressing_section = \
        {
            'type': 'section',
            'fields': []  # list of AlertFields
        }

    improving_section = \
        {
            'type': 'section',
            'fields': []  # list of AlertFields
        }

    constant_section = \
        {
            'type': 'section',
            'fields': []  # list of AlertFields
        }

    # lists of tuples
    first_alerts_stations = []
    regressing_stations = []
    improving_stations = []
    constant_stations = []


    def change_header_text(self, msg):
        self.header_section['text']['text'] = msg

    def get_payload(self):
        alert_required = False
        self.blocks['blocks'] = [self.header_section]
        if len(self.first_alerts_stations) > 0:
            msg = self.build_alert_msg('First Appearance', self.first_alerts_stations)
            sf = self.get_slack_field(msg)
            self.first_alerts_section['fields'].append(sf)
            self.blocks['blocks'].append(self.first_alerts_section)
            alert_required = True
        if len(self.regressing_stations) > 0:
            msg = self.build_alert_msg('Regressing Stations', self.regressing_stations)
            sf = self.get_slack_field(msg)
            self.regressing_section['fields'].append(sf)
            self.blocks['blocks'].append(self.regressing_section)
            alert_required = True
        if len(self.improving_stations) > 0:
            msg = self.build_alert_msg('Improving Stations', self.improving_stations)
            sf = self.get_slack_field(msg)
            self.improving_section['fields'].append(sf)
            self.blocks['blocks'].append(self.improving_section)
            alert_required = True
        if len(self.constant_stations) > 0:
            msg = self.build_alert_msg('Constant Stations', self.constant_stations)
            sf = self.get_slack_field(msg)
            self.constant_section['fields'].append(sf)
            self.blocks['blocks'].append(self.constant_section)
        if alert_required is False:
            return False
        return self.blocks

    def build_alert_msg(self, section, stn_list):
        msg = f'*{section}*\n'
        for stn in stn_list:
            msg += f'{stn[0]}, {stn[1]}\n'
        return msg

    def get_slack_field(self, msg):
        return {
            'type': 'mrkdwn',  # hardcode to markdown for now
            'text': msg  # downtime
        }

    def get_slack_header(self, msg):
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": msg
            }
        }



def get_slack_field(msg):
    return {
        'type': 'mrkdwn',  # hardcode to markdown for now
        'text': msg  # downtime
    }

def get_slack_header(msg):
    return {
		"type": "header",
		"text": {
			"type": "plain_text",
			"text": msg
		}
	}

def bud_monitor(virtual_net='PACNW', network='UO'):
    monitor_stn_list = {}

    resp = requests.get(f"http://buddy.iris.washington.edu/bud_stuff/dmc/bud_monitor.{virtual_net}.html")

    virtnet_soup = BeautifulSoup(resp.text, "html.parser")

    legend_table = virtnet_soup.find_all("table", {"class": "legend"})
    legend = {}
    for key in legend_table[0].find_all('td'):
        # print(f"{key['bgcolor']} {html.unescape(key.text).strip()}")
        legend[key['bgcolor']] = html.unescape(key.text).strip()

    network_table = None
    get_next_table = False

    for child in virtnet_soup.html.body.p.children:
        if get_next_table is True and child.name == 'table':
            network_table = child
            break
        if child.name == 'a' and child.has_attr('name') and child['name'] == network:
            get_next_table = True

    net_found = False
    for td in network_table.findAll('td'):
        if not net_found and re.search(network, td.a.text):
            net_found = True
            continue
        monitor_stn_list[td.a.text] = downtime.index(legend[td['bgcolor']])

    return monitor_stn_list


def bud_mda(network='UO'):
    now = datetime.date.today()

    mda = requests.get(f"http://ds.iris.edu/mda/{network}/")

    mda_bs4 = BeautifulSoup(mda.text, 'html.parser')

    mda_table = mda_bs4.find("table", {"class": "table-mda"})

    mda_table_rows = mda_table.tbody.find_all("tr")

    mda_stns = []
    for row in mda_table_rows:
        cells = row.find_all("td")

        # determine end time in fourth column
        more_data = cells[3].find("li")
        if more_data is not None:
            y, m, d = more_data.text.strip().split('-')
            end_date = datetime.date(int(y), int(m), int(d))
        else:
            y, m, d = cells[3].text.strip().split('-')
            end_date = datetime.date(int(y), int(m), int(d))

        if end_date > now:
            mda_stns.append(cells[0].text.strip())

    return mda_stns



if __name__ == "__main__":
    network = "UO"
    vn = "PACNW"
    output_file = Path('output.json')

    now = datetime.datetime.now(timezone.utc)

    mda_stns = bud_mda(network=network)
    monitor_stns = bud_monitor(virtual_net=vn, network=network)

    report_new = {
        'update_time': now.isoformat(),
        'stations': {}
              }

    # stations drop out of reporting if downtime >5 days.  Compare against the mda list (includes all stations)
    for stn in mda_stns:
        if stn not in monitor_stns:
            report_new['stations'][stn] = {'downtime': 12, 'alert': False}

    for stn in monitor_stns:
        if monitor_stns[stn] > threshold:
            # print(f'{stn} {downtime[monitor_stns[stn]]}')
            report_new['stations'][stn] = {'downtime': monitor_stns[stn], 'alert': False}

    slack_payload = SlackAlertPayload()

    if not output_file.exists():
        slack_payload.change_header_text(f'Initial Execution\n{now.isoformat()}')
        # first time running, create output.log and alert all
        for stn, values in report_new['stations'].items():
            print(f'{stn} new this epoch, {downtime[values["downtime"]]}')
            slack_payload.first_alerts_stations.append((stn, downtime[values["downtime"]]))

    else:
        slack_payload.change_header_text(now.isoformat())
        # compare
        last_alert_json = None
        with open(output_file, 'r') as f:
            last_alert_json = json.load(f)

        # stations alerting
        for stn, values in report_new['stations'].items():
            if stn in last_alert_json['stations']:
                # stations improving
                if values['downtime'] < last_alert_json['stations'][stn]['downtime']:
                    print(f'{stn} improved {downtime[values["downtime"]]}, {downtime[last_alert_json["stations"][stn]["downtime"]]}')
                    # only alert once if station is improving
                    if last_alert_json['stations'][stn]['alert'] is True:
                        slack_payload.improving_stations.append((stn, downtime[values["downtime"]]))
                    report_new['stations'][stn]["alert"] = False
                # stations regressing
                elif values['downtime'] > last_alert_json['stations'][stn]['downtime']:
                    print(f'{stn} regressed {downtime[values["downtime"]]}, {downtime[last_alert_json["stations"][stn]["downtime"]]}')
                    slack_payload.regressing_stations.append((stn, downtime[values["downtime"]]))
                    report_new['stations'][stn]["alert"] = True
                # stations constant
                else:
                    print(
                        f'{stn} no change {downtime[values["downtime"]]}')
                    slack_payload.constant_stations.append((stn, downtime[values["downtime"]]))
                    report_new['stations'][stn]["alert"] = last_alert_json['stations'][stn]['alert']
            # first alert
            else:
                print(f'{stn} new this epoch, {downtime[values["downtime"]]}')
                slack_payload.first_alerts_stations.append((stn, downtime[values["downtime"]]))
                report_new['stations'][stn]["alert"] = True


        # stations returning to no latency, don't store these, but alert one last time
        for stn, values in last_alert_json['stations'].items():
            if stn not in report_new['stations']:
                print(f'{stn} returned to minimal latency')
                if values['alert'] is True:
                  slack_payload.improving_stations.append((stn, downtime[0]))

    # build slack alert
    payload = slack_payload.get_payload()
    print(payload)
    if payload is not False:
        # send slack msg
        resp = requests.post(url=slack_webhook, headers=slack_webhook_headers, data=str(payload))
        print(resp)
    else:
        print("alert not required")

    with open(output_file, 'w') as f:
        f.write(json.dumps(report_new, indent=4, sort_keys=True))
