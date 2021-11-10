import requests
import re


from bs4 import BeautifulSoup

bud_url = 'http://buddy.iris.washington.edu/bud_stuff/dmc/bud_monitor.ALL.html'

class BudParser():
    def __init__(self, page = bud_url):
        resp = requests.get(page)
        self.soup = BeautifulSoup(resp.text, 'html.parser')
        self.legend = None

    # def get_network_table(self, network):
    #     pattern = "/bud_stuff/bud/bud_data.pl?YEAR=2021&amp;JDAY=309&amp;STA=WMZ&amp;LOC=*&amp;CHAN=*&amp;WIGGLES=on&amp;FTP=on&amp;BUDDIR=/budnas/virtualnets/ALL&amp;GOAT=on&amp;NETLIST=AR;&amp;SHOW_BY=CHAN&amp;SHOW_DATA_LATENCY=on&amp;SHOW_FEED_LATENCY=on"
    #     net_tbl = self.soup.find(href=f'/bud_stuff/network_info/{network}.html')
    #     return net_tbl.parent.parent

    def get_status(self, network, station):
        if self.legend is None:
            self.retrieve_legend()

        keys = list(self.legend.keys())
        colors = [tup[0] for tup in self.legend.values()]

        re_exp = re.compile(f"^(?=.*NETLIST={network})(?=.*STA={station}&).*$")
        matches = self.soup.find_all(href=re_exp)
        if len(matches) > 0:
            level = keys[colors.index(matches[0].parent["bgcolor"])]
            return level, self.legend[level][1]
        else:
            raise UserWarning(f"unable to find {network}, {station}")

    def retrieve_legend(self):

        # return dictionary { level(int): (color(str), downtime(str))...}
        self.legend = {}
        legend_table = self.soup.find_all('table', class_='legend')[0]
        level = 0
        for cell in legend_table.find_all('td'):
            self.legend[level] = (cell['bgcolor'], cell.b.string)
            level += 1
        self.legend[level] = (None, "> 10 days")
        return self.legend

    def level2downtime(self, level:int):
        if self.legend is None:
            self.retrieve_legend()

        if level is None:
            return ''
        elif level < 0:
            return ''
        else:
            return self.legend[level][1]
    
    def get_level2downtime_table(self):
        legend = self.retrieve_legend()
        table = {}
        for level, values in legend.items():
            table[level] = values[1]

        return table
    
    def get_downtime_dict(self, station_list):
        downtime_dict = {}
        for station in station_list:
            try:
                downtime_dict[station] = self.get_status(station[0], station[1])[0]
            except UserWarning as e:
                # station not found in BUD, downtime is > 10 days
                downtime_dict[station] = len(self.legend)-1

        return downtime_dict
    

if __name__ == "__main__":
    blah = BudParser()
    legend = blah.retrieve_legend()
    print(legend)

    print(blah.level2downtime(4))
    print(blah.get_status('UW', 'MCLN'))
    
