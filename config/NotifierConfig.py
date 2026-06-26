from dataclasses import dataclass

from config.ConfigBasic import BasicConfig, config_field, str_to_bool


@dataclass(slots=True)
class NotifierConfig(BasicConfig):
    """Notification channels used after success or proxy exhaustion."""

    serverchan_key: str = config_field(
        "",
        env="BTB_SERVERCHANKEY",
        runtime="serverchanKey",
        cli="--notifier-config.serverchan-key",
    )
    """ServerChan Turbo send key."""

    serverchan3_api_url: str = config_field(
        "",
        env="BTB_SERVERCHAN3APIURL",
        runtime="serverchan3ApiUrl",
        cli="--notifier-config.serverchan3-api-url",
    )
    """ServerChan3 API endpoint."""

    pushplus_token: str = config_field(
        "",
        env="BTB_PUSHPLUSTOKEN",
        runtime="pushplusToken",
        cli="--notifier-config.pushplus-token",
    )
    """PushPlus token."""

    bark_token: str = config_field(
        "",
        env="BTB_BARKTOKEN",
        runtime="barkToken",
        cli="--notifier-config.bark-token",
    )
    """Bark token or self-hosted Bark push path."""

    ntfy_url: str = config_field(
        "",
        env="BTB_NTFY_URL",
        runtime="ntfy_url",
        cli="--notifier-config.ntfy-url",
    )
    """ntfy topic URL."""

    ntfy_username: str = config_field(
        "",
        env="BTB_NTFY_USERNAME",
        runtime="ntfy_username",
        cli="--notifier-config.ntfy-username",
    )
    """Username for ntfy authentication."""

    ntfy_password: str = config_field(
        "",
        env="BTB_NTFY_PASSWORD",
        runtime="ntfy_password",
        cli="--notifier-config.ntfy-password",
    )
    """Password for ntfy authentication."""

    meow_nickname: str = config_field(
        "",
        env="BTB_MEOWNICKNAME",
        runtime="meowNickname",
        cli="--notifier-config.meow-nickname",
    )
    """MeoW nickname."""

    audio_path: str = config_field(
        "",
        env="BTB_AUDIO_PATH",
        runtime="audio_path",
        cli="--notifier-config.audio-path",
    )
    """Local audio file played after success."""

    notify_proxy_exhausted: bool = config_field(
        False,
        env="BTB_NOTIFY_PROXY_EXHAUSTED",
        runtime="notify_proxy_exhausted",
        cast=str_to_bool,
        cli_true="--notifier-config.notify-proxy-exhausted",
    )
    """Send a notification when all proxies enter cooldown."""
