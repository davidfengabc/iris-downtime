import requests
import re
import html
import datetime

from bs4 import BeautifulSoup

downtime = [
    "< 1 min",
    "≥ 1 min",
    "> 10 min",
    "> 30 min",
    "> 1 hour",
    "> 2 hours",
    "> 6 hours",
    "> 1 day",
    "> 2 days",
    "> 3 days",
    "> 4 days",
    "> 5 days"
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

    mda_stns = bud_mda(network=network)
    monitor_stns = bud_monitor(virtual_net=vn, network=network)

    for stn in mda_stns:
        if stn not in monitor_stns:
            print(f'{stn} not found')

    for stn in monitor_stns:
        if monitor_stns[stn] > 0:
            print(f'{stn} {downtime[monitor_stns[stn]]}')
