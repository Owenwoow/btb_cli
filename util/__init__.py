import os
import re
import sys
import time
from loguru import logger
from util.TimeUtil import TimeUtil


def get_exec_path() -> str:
    if len(sys.argv[0]) > 0 and sys.argv[0].endswith(".py"):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    else:
        return os.path.dirname(os.path.realpath(sys.executable))


EXE_PATH: str = get_exec_path()
LOG_DIR: str = os.environ.get("BTB_LOG_DIR", os.path.join(EXE_PATH, "btb_logs"))
os.makedirs(LOG_DIR, exist_ok=True)

# 初始化 loguru 日志
log_file_name = os.environ.get("BTB_APP_LOG_NAME", "app.log")
log_file_name = re.sub(r"[^\w.\-]", "_", log_file_name) or "app.log"
log_file_path = os.path.join(LOG_DIR, log_file_name)
logger.add(
    log_file_path,
    rotation="50 MB",
    retention="7 days",
    encoding="utf-8",
    level="DEBUG",
    colorize=False,
)

# NTP 时间校准
time_service = TimeUtil()
time_service.set_timeoffset(time_service.compute_timeoffset())

__all__ = ["EXE_PATH", "LOG_DIR", "time_service"]
