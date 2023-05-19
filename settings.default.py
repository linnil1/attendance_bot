import logging

logging.basicConfig(level=logging.DEBUG)

line_token = ""
line_webhook = ""
line_your_id = ""  # your lineID (mostly for testing)
port = 10101
mode = "prod"  # "prod", "test"
db = "redis"  # "redis" "object"
redis_url = f"redis://redis:6379/{mode}"
