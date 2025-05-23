[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)

# Dynamic Timers
A Python Django web based program to run one or multiple timers. Give your timers a name and track your time spend.

## Getting started
Create a `.env` file in the project root and add the following variables.
|ENV var|Explain|
|-------|-------|
|SECRET_KEY|The secret key for Django to use for signing, hashing and signing|
|ALLOWED_HOSTS|The host names that are allowed for the app|
|LOG_LEVEL|The log level, allowed values are: DEBUG, INFO, WARNING, ERROR, or CRITICAL|


## Setup the environment
Create the python environment and install required packages, in these examples the project root is expected to be `/var/www/`, change where necessary.
```
cd /var/www/dynamic-timers/
python3.10 -m venv env
source env/bin/activate
pip install -r requirements.txt
deactivate
```


## Setup Django
Run the following commands to initialize Django.
```
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

## Run locally
```
# Run the program
/var/www/dynamic-timers/env/bin/python3 /var/www/dynamic-timers/manage.py runserver
# or
source /var/www/dynamic-timers/env/bin/activate
python3 /var/www/dynamic-timers/manage.py runserver
```

## Run as systemd with Nginx reverse proxy
Copy the service file and enable the service.
```
cp /var/www/dynamic-timers/assets/dynamic-timers.service /etc/systemd/system/dynamic-timers.service
sudo systemctl daemon-reload
sudo systemctl start dynamic-timers
sudo systemctl enable dynamic-timers
```

Copy the Nginx config and start the proxy.
```
cp /var/www/dynamic-timers/assets/dynamic-timers.conf /etc/nginx/sites-available/dynamic-timers.conf
sudo ln -s /etc/nginx/sites-available/dynamic-timers /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```
