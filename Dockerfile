FROM python:3.11
RUN pip install line-bot-sdk flask[async] redis orjson
WORKDIR /app
