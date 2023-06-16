import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("attendence")
logger.setLevel(level=logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

line_token = ""
line_webhook = ""
line_your_id = ""  # your lineID (mostly for testing)
port = 10101
mode = "prod"  # "prod", "test"
db = "object"  # "redis" "object" "dynamodb"

# redis
redis_url = f"redis://redis:6379/attendence-{mode}"

# dynamodb
dynamodb_table = f"attendence-{mode}"
dynamodb_other = dict(
    BillingMode="PAY_PER_REQUEST",
    Tags=[
        {"Key": "project", "Value": "attendence"},
    ],
)
