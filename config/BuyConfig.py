from dataclasses import dataclass
import os
from typing import ClassVar

from config.ConfigBasic import (
    BasicConfig,
    DEFAULT_CREATE_REQUEST_BATCH_SIZE,
    DEFAULT_CREATE_RETRY_LIMIT,
    config_field,
    nested_config_field,
    normalize_log_level,
    str_to_bool,
)
from config.NotifierConfig import NotifierConfig
from util.Constant import DEFAULT_RATE_LIMIT_DELAY_MS


@dataclass(slots=True)
class BuyConfig(BasicConfig):
    """Ticket buying runtime configuration."""

    _skip_cli_fields: ClassVar[set[str]] = {"tickets_info", "config_file"}

    tickets_info: str = ""
    """Ticket JSON content passed to the buyer."""

    config_file: str = config_field(
        "",
        cli="--config-file",
    )
    """Path to a ticket configuration JSON file."""

    time_start: str = config_field(
        "",
        env="BTB_TIME_START",
        runtime="time_start",
        cli="--time-start",
    )
    """Scheduled start time, for example 2026-06-18T20:00:00."""

    interval: int | None = config_field(
        1000,
        env="BTB_INTERVAL",
        runtime="interval",
        cli="--interval",
        cast=int,
    )
    """Default request interval in milliseconds."""

    notifier_config: NotifierConfig = nested_config_field(NotifierConfig)
    """Notification settings."""

    https_proxys: str = config_field(
        "none",
        env="BTB_HTTPS_PROXYS",
        runtime="https_proxys",
        cli="--https-proxys",
    )
    """Proxy string or comma-separated proxy pool."""

    proxy_api_url: str = config_field(
        "",
        env="BTB_PROXY_API_URL",
        runtime="proxy_api_url",
        cli="--proxy-api-url",
    )
    """Proxy provider API URL used to replenish the proxy pool."""

    proxy_api_protocol: str = config_field(
        "http",
        env="BTB_PROXY_API_PROTOCOL",
        runtime="proxy_api_protocol",
        cli="--proxy-api-protocol",
    )
    """Proxy provider protocol parameter: http or socks5."""

    proxy_api_request_count: int = config_field(
        0,
        env="BTB_PROXY_API_REQUEST_COUNT",
        runtime="proxy_api_request_count",
        cli="--proxy-api-request-count",
        cast=int,
    )
    """Number of proxies requested from the API; 0 follows the current pool size."""

    show_random_message: bool = config_field(
        True,
        runtime="show_random_message",
        cast=str_to_bool,
        cli_false="--no-show-random-message",
    )
    """Show random failure messages after a round fails."""

    show_qrcode: bool = config_field(
        True,
        runtime="show_qrcode",
        cast=str_to_bool,
        cli_false="--no-show-qrcode",
    )
    """Show the payment QR code after a successful order."""

    create_retry_limit: int = config_field(
        DEFAULT_CREATE_RETRY_LIMIT,
        env="BTB_CREATE_RETRY_LIMIT",
        runtime="create_retry_limit",
        cli="--create-retry-limit",
        cast=int,
    )
    """Maximum create-order attempts per round."""

    create_request_batch_size: int = config_field(
        DEFAULT_CREATE_REQUEST_BATCH_SIZE,
        env="BTB_CREATE_REQUEST_BATCH_SIZE",
        runtime="create_request_batch_size",
        cli="--create-request-batch-size",
        cast=int,
    )
    """Number of create-order requests sent in one batch."""

    rate_limit_delay_ms: int = config_field(
        DEFAULT_RATE_LIMIT_DELAY_MS,
        env="BTB_RATE_LIMIT_DELAY_MS",
        runtime="rate_limit_delay_ms",
        cli="--rate-limit-delay-ms",
        cast=int,
    )
    """Delay after receiving HTTP 429, in milliseconds."""

    refresh_interval_min_count: int = config_field(
        10,
        env="BTB_REFRESH_INTERVAL_MIN_COUNT",
        runtime="refresh_interval_min_count",
        cli="--refresh-interval-min-count",
        cast=int,
    )
    """循环内主动复检项目详情的最小 create 次数。"""

    refresh_interval_max_count: int = config_field(
        30,
        env="BTB_REFRESH_INTERVAL_MAX_COUNT",
        runtime="refresh_interval_max_count",
        cli="--refresh-interval-max-count",
        cast=int,
    )
    """循环内主动复检项目详情的最大 create 次数。"""

    proxy_max_consecutive_failures: int = config_field(
        10,
        env="BTB_PROXY_MAX_CONSECUTIVE_FAILURES",
        runtime="proxy_max_consecutive_failures",
        cli="--proxy-max-consecutive-failures",
        cast=int,
    )
    """Failures before one proxy is temporarily cooled down."""

    proxy_cooldown_seconds: int = config_field(
        60,
        env="BTB_PROXY_COOLDOWN_SECONDS",
        runtime="proxy_cooldown_seconds",
        cli="--proxy-cooldown-seconds",
        cast=int,
    )
    """Cooldown duration for a failed proxy, in seconds."""

    proxy_backoff_max_seconds: int = config_field(
        240,
        env="BTB_PROXY_BACKOFF_MAX_SECONDS",
        runtime="proxy_backoff_max_seconds",
        cli="--proxy-backoff-max-seconds",
        cast=int,
    )
    """Maximum sleep time when the whole proxy pool is unavailable."""

    auto_open_payment_url: bool = config_field(
        False,
        runtime="auto_open_payment_url",
        cast=str_to_bool,
        cli_true="--auto-open-payment-url",
    )
    """Open the payment page automatically after success."""

    log_level: str = config_field(
        "standard",
        env="BTB_LOG_LEVEL",
        runtime="log_level",
        cli="--log-level",
        cast=normalize_log_level,
    )
    """Console logging preset: simple, standard, or debug."""

    def _resolved_tickets_info(self) -> str:
        if self.config_file:
            config_path = os.path.expanduser(self.config_file)
            with open(config_path, "r", encoding="utf-8") as config_file:
                return config_file.read()
        return self.tickets_info

    def resolved_config(self) -> "BuyConfig":
        return self.with_overrides(tickets_info=self._resolved_tickets_info())
