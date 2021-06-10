# iris-downtime
```
git clone https://github.com/davidfengabc/iris-downtime.git
cd iris-downtime/
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```
# set slack_webhook and threshold variables in script
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
*/30 * * * * /home4/dfeng/iris-downtime/venv/bin/python3 bud-compare.py
```
