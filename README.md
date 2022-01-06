# iris-downtime
```
git clone https://github.com/pnsn/iris-downtime.git
cd iris-downtime/
git switch classify
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```
# edit config.json to include/exclude networks/stations
# create secrets.json in same directory as bud-compare.py
IRIS_DOWNTIME_CHANNEL is the name of the channel.  The app must be added to the channel as an integration.
IRIS_DOWNTIME_TOKEN is an oauth token provided by Slack.

```
{
    "IRIS_DOWNTIME_CHANNEL": "", 
    "IRIS_DOWNTIME_TOKEN": ""
}
```
# run once
```
python3 bud-compare.py
```
# setup crontab
```
crontab -e
```
# add line to crontab file, run script every 30 min
```
*/30 * * * * cd /home4/dfeng/iris-downtime && /home4/dfeng/iris-downtime/venv/bin/python3 /home4/dfeng/iris-downtime/bud-compare.py
```
