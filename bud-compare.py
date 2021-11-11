import budc.budc as budc
import budc.config as config
import budc.generator as generator
import budc.slackint as slackint
import datetime
import logging
import os
import json

secrets = json.load(open('secrets.json'))
channel = secrets["IRIS_DOWNTIME_CHANNEL"]
token = secrets["IRIS_DOWNTIME_TOKEN"]

logging.basicConfig(format='%(asctime)s %(message)s', filename='logger.log', level=logging.DEBUG)

logging.info(f'Starting')
now = datetime.datetime.now()

bc = config.BudConfig('config.json')
logging.debug(f'budconfig stations: {bc.get_stations()}')
bparser = budc.BudParser()

legend = bparser.get_level2downtime_table()
logging.debug(legend)

stations = bc.get_stations()
logging.debug(stations)

downtime_dict = bparser.get_downtime_dict(stations)

bgen = generator.Generator(downtime_dict, bc.get_downtime_threshold(), bc.get_elapsed_threshold())

alert_status = bgen.decider()

alert = bgen.get_alert()
logging.debug(alert)


if alert_status == 1:
    #update previous alert
    logging.info('update previous alert')
    slack = slackint.SlackInterface(bgen, legend, channel, token)
    ts = bgen.get_previous_alert_id()

    # retain timestamp from original alert
    orig_ts = bgen.get_previous_timestamp()
    status, ts = slack.update_alert(ts)
    # don't save updates, otherwise new alerts will be missed
    #bgen.save_alert(ts)
    logging.debug(f'alert_status {alert_status}, status {status}, ts {ts}')
elif alert_status == 2:
    #generate new alert
    logging.info('generate new alert')
    slack = slackint.SlackInterface(bgen, legend, channel, token)
    status, ts = slack.new_alert()
    bgen.save_alert(ts)
    logging.debug(f'alert_status {alert_status}, status {status}, ts {ts}')
else:
    #do nothing, don't even save it
    logging.info('no action required')
    pass

logging.info('END')

