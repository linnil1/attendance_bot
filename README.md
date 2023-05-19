# Attendence Bot

This project is built for fun.

All the data is save in the NoSQL style (redis).

Using LineBot as interface. (and use one of important feature: option selection)

Line bot can customize MENU for every client!
Create one for this app by running `menu.py`


## Start

Environemt:
* Python 3.11
* line-bot-sdk
* redis

```
# modify the settings
cp settings.default.py settings.py

# and run it
docker compose up -d
```


## Demo

![demo](https://raw.githubusercontent.com/linnil1/attendance_bot/main/demo.jpg)


