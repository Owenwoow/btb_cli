import datetime


BEIJING_TZ = datetime.timezone(datetime.timedelta(hours=8), name="Asia/Shanghai")
DEFAULT_REQUEST_INTERVAL = 1000
DEFAULT_CREATE_REQUEST_BATCH_SIZE = 3
DEFAULT_PROXY_MAX_CONSECUTIVE_FAILURES = 2
DEFAULT_PROXY_COOLDOWN_SECONDS = 180
DEFAULT_PROXY_BACKOFF_MAX_SECONDS = 600
DEFAULT_LOG_RETENTION_DAYS = 7
DEFAULT_RATE_LIMIT_DELAY_MS = 100
BASE_URL = "https://show.bilibili.com"
WARMUP_AT_SECONDS = 5.0
DEFAULT_CREATE_RETRY_LIMIT = 20
MEOW_API_BASE = "https://api.chuckfang.com"
DEFAULT_TIMEOUT = (3.05, 8)
H2_TIMEOUT = {
    "connect": 3.05,
    "read": 5.0,
    "write": 5.0,
    "pool": 5.0,
}
H2_LIMITS = {
    "max_keepalive_connections": 10,
    "max_connections": 20,
    "keepalive_expiry": 60.0,
}
