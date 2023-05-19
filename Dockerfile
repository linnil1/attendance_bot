FROM python:3.11
RUN pip install line-bot-sdk flask[async] redis orjson pottery pillow pytest
WORKDIR /app
