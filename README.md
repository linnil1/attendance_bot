# Attendence Bot

This project is built for fun.

All the data is save in the NoSQL style (redis, DynamoDB).

Using LineBot as interface. (and use one of Line's important feature: (menu, option selection)

Line bot can customize MENU for every client!
Create one for this app by running `python menu.py`


## Line bot creation
Go to LINE Developer setting (https://developers.line.biz/console/)

Providers -> Select yourself -> Channel -> Create channel -> Message API > Use Webhook > webhook URL -> https://your\_url/callback

Put `Channel secret` (In basic) to `line_webook` and
`Channel access token` (In Messaging API) to `line_token` in `settings.py`


## Start

Environemt:
* Python 3.11
* redis or DynamoDB

```
# modify the settings
cp settings.default.py settings.py

# and run it in Docker
docker compose up -d
```


## Deploy

I currently deploy on aws DynamoDB, lambda, API Gateway using Zappa (https://github.com/zappa/Zappa).

In short, Zappa create a serverless WSGI to handle Flask app and deploy them (including packages) to Lambda.
And then, corresponded CloudWatch, API Gateway are also setup.

```
mkdir deploy
cd deploy
cp ../*.py .
cp ../zappa_settings.json .
zappa deploy dev
```

Then, rename your webhook url (In LINE) to `https://{restapi_id}.execute-api.{region}.amazonaws.com/dev/callback`

or add your custom domain to API Gateway by assigning `domain` and `certificate_arn` in `zappa_settings.json`.


## Demo

![demo](https://github.com/linnil1/attendance_bot/blob/main/demo.jpg?raw=true)
