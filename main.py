#!/usr/bin/env python3
"""
btb_cli — B站抢票 CLI 独立版入口

用法:
    python main.py --config-file 订单.json [选项]
    python main.py --config-file 订单.json --time-start 2026-06-28T20:00:00
    python main.py --config-file 订单.json --https-proxys http://user:pass@1.2.3.4:7890
    python main.py --config-file 订单.json --notifier-config.bark-token YOUR_BARK_TOKEN

订单 JSON 格式（与原项目 biliTickerBuy 兼容）：
    {
        "detail": "演唱会名称",
        "count": 1,
        "screen_id": 123456,
        "project_id": 654321,
        "sku_id": 111111,
        "pay_money": 38000,
        "order_type": 1,
        "buyer_info": [...],
        "buyer": "姓名",
        "tel": "13800000000",
        "deliver_info": {...},
        "cookies": [{"name": "SESSDATA", "value": "xxx"}, ...]
    }
"""
import argparse
import json
import os
import sys

# 确保 btb_cli 目录在 sys.path 中（支持直接运行和从其他目录调用）
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# Windows 控制台默认可能是 GBK，中文 help / 日志 / 二维码会抛 UnicodeEncodeError。
# 统一切到 UTF-8（Python 3.7+ 支持 reconfigure），失败则忽略。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from loguru import logger


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="btb_cli",
        description="B站会员购抢票 CLI 工具（独立版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 订单配置
    ticket_group = parser.add_argument_group("订单配置")
    ticket_group.add_argument(
        "--config-file",
        metavar="PATH",
        default="",
        help="票务 JSON 配置文件路径（与 --tickets-info 二选一）",
    )
    ticket_group.add_argument(
        "--tickets-info",
        metavar="JSON",
        default="",
        help="直接传入票务 JSON 字符串（与 --config-file 二选一）",
    )

    # 抢票参数
    grab_group = parser.add_argument_group("抢票参数")
    grab_group.add_argument(
        "--time-start",
        metavar="DATETIME",
        default="",
        help="开抢时间，格式: 2026-06-28T20:00:00（留空立即开始）",
    )
    grab_group.add_argument(
        "--interval",
        type=int,
        default=1000,
        metavar="MS",
        help="请求间隔，单位毫秒，默认 1000",
    )
    grab_group.add_argument(
        "--create-retry-limit",
        type=int,
        default=20,
        metavar="N",
        help="每轮创建订单最大重试次数，默认 20",
    )
    grab_group.add_argument(
        "--create-request-batch-size",
        type=int,
        default=3,
        metavar="N",
        help="批量并发创建请求数，默认 3",
    )
    grab_group.add_argument(
        "--rate-limit-delay-ms",
        type=int,
        default=100,
        metavar="MS",
        help="收到 HTTP 429 后冷却时长（毫秒），默认 100。调大更稳（可设为等于 --interval）",
    )
    grab_group.add_argument(
        "--refresh-interval-min-count",
        type=int,
        default=10,
        metavar="N",
        help="循环内主动复检项目详情的最小 create 次数，默认 10",
    )
    grab_group.add_argument(
        "--refresh-interval-max-count",
        type=int,
        default=30,
        metavar="N",
        help="循环内主动复检项目详情的最大 create 次数，默认 30；设为 0 关闭周期复检",
    )
    grab_group.add_argument(
        "--no-show-qrcode",
        action="store_true",
        help="抢票成功后不弹出二维码窗口",
    )
    grab_group.add_argument(
        "--auto-open-payment-url",
        action="store_true",
        help="抢票成功后自动在浏览器打开支付链接",
    )
    grab_group.add_argument(
        "--no-show-random-message",
        action="store_true",
        help="失败时不显示随机提示语",
    )

    # 代理
    proxy_group = parser.add_argument_group("代理设置")
    proxy_group.add_argument(
        "--https-proxys",
        metavar="PROXY",
        default="none",
        help="代理地址，多个用逗号分隔。留空或 none 表示直连。示例: http://127.0.0.1:7890",
    )
    proxy_group.add_argument(
        "--proxy-max-consecutive-failures",
        type=int,
        default=10,
        metavar="N",
        help="单个代理连续失败多少次后冷却，默认 10",
    )
    proxy_group.add_argument(
        "--proxy-cooldown-seconds",
        type=int,
        default=60,
        metavar="S",
        help="代理冷却时长（秒），默认 60",
    )
    proxy_group.add_argument(
        "--proxy-backoff-max-seconds",
        type=int,
        default=240,
        metavar="S",
        help="代理全部失效时最大休眠时长（秒），默认 240",
    )
    proxy_group.add_argument(
        "--proxy-api-url",
        metavar="URL",
        default="",
        help="代理供应商 API 地址；代理池全部失效时自动拉取新代理补池。留空则不启用",
    )
    proxy_group.add_argument(
        "--proxy-api-protocol",
        choices=["http", "socks5"],
        default="http",
        help="代理 API 返回代理的协议，默认 http",
    )
    proxy_group.add_argument(
        "--proxy-api-request-count",
        type=int,
        default=0,
        metavar="N",
        help="每次从代理 API 拉取的数量，0 表示跟随当前代理池大小",
    )

    # 推送通知
    notify_group = parser.add_argument_group("推送通知")
    notify_group.add_argument(
        "--notifier-config.serverchan-key",
        dest="notifier_serverchan_key",
        metavar="KEY",
        default="",
        help="Server酱 Turbo SendKey",
    )
    notify_group.add_argument(
        "--notifier-config.serverchan3-api-url",
        dest="notifier_serverchan3_api_url",
        metavar="URL",
        default="",
        help="Server酱³ API URL",
    )
    notify_group.add_argument(
        "--notifier-config.pushplus-token",
        dest="notifier_pushplus_token",
        metavar="TOKEN",
        default="",
        help="PushPlus Token",
    )
    notify_group.add_argument(
        "--notifier-config.bark-token",
        dest="notifier_bark_token",
        metavar="TOKEN",
        default="",
        help="Bark Token 或自托管地址",
    )
    notify_group.add_argument(
        "--notifier-config.ntfy-url",
        dest="notifier_ntfy_url",
        metavar="URL",
        default="",
        help="ntfy Topic URL",
    )
    notify_group.add_argument(
        "--notifier-config.ntfy-username",
        dest="notifier_ntfy_username",
        metavar="USER",
        default="",
        help="ntfy 用户名",
    )
    notify_group.add_argument(
        "--notifier-config.ntfy-password",
        dest="notifier_ntfy_password",
        metavar="PASS",
        default="",
        help="ntfy 密码",
    )
    notify_group.add_argument(
        "--notifier-config.meow-nickname",
        dest="notifier_meow_nickname",
        metavar="NICK",
        default="",
        help="MeoW 昵称",
    )
    notify_group.add_argument(
        "--notifier-config.audio-path",
        dest="notifier_audio_path",
        metavar="PATH",
        default="",
        help="抢票成功时播放的本地音频文件路径",
    )
    notify_group.add_argument(
        "--notifier-config.notify-proxy-exhausted",
        dest="notifier_notify_proxy_exhausted",
        action="store_true",
        help="代理全部失效时发送推送通知",
    )

    # 日志 / 显示
    log_group = parser.add_argument_group("日志 / 显示")
    log_group.add_argument(
        "--log-level",
        choices=["simple", "standard", "debug"],
        default="standard",
        help="日志级别: simple / standard / debug，默认 standard",
    )
    log_group.add_argument(
        "--no-tui",
        action="store_true",
        help="禁用 Textual 终端 UI，改用纯文本日志输出（适合重定向/无法渲染的终端）",
    )

    return parser


def _build_config_from_args(args: argparse.Namespace):
    """将命令行参数转换为 BuyConfig 对象。"""
    from config.BuyConfig import BuyConfig
    from config.NotifierConfig import NotifierConfig

    notifier_config = NotifierConfig(
        serverchan_key=args.notifier_serverchan_key,
        serverchan3_api_url=args.notifier_serverchan3_api_url,
        pushplus_token=args.notifier_pushplus_token,
        bark_token=args.notifier_bark_token,
        ntfy_url=args.notifier_ntfy_url,
        ntfy_username=args.notifier_ntfy_username,
        ntfy_password=args.notifier_ntfy_password,
        meow_nickname=args.notifier_meow_nickname,
        audio_path=args.notifier_audio_path,
        notify_proxy_exhausted=args.notifier_notify_proxy_exhausted,
    )

    tickets_info = args.tickets_info or ""
    config_file = args.config_file or ""

    return BuyConfig(
        tickets_info=tickets_info,
        config_file=config_file,
        time_start=args.time_start,
        interval=args.interval,
        notifier_config=notifier_config,
        https_proxys=args.https_proxys,
        proxy_api_url=args.proxy_api_url,
        proxy_api_protocol=args.proxy_api_protocol,
        proxy_api_request_count=args.proxy_api_request_count,
        show_random_message=not args.no_show_random_message,
        show_qrcode=not args.no_show_qrcode,
        create_retry_limit=args.create_retry_limit,
        create_request_batch_size=args.create_request_batch_size,
        rate_limit_delay_ms=args.rate_limit_delay_ms,
        refresh_interval_min_count=args.refresh_interval_min_count,
        refresh_interval_max_count=args.refresh_interval_max_count,
        proxy_max_consecutive_failures=args.proxy_max_consecutive_failures,
        proxy_cooldown_seconds=args.proxy_cooldown_seconds,
        proxy_backoff_max_seconds=args.proxy_backoff_max_seconds,
        auto_open_payment_url=args.auto_open_payment_url,
        log_level=args.log_level,
    )


def _resolve_log_level(raw: str) -> str:
    log_level = str(raw or "standard").lower()
    return "DEBUG" if log_level == "debug" else "INFO"


def _setup_logging(*, console_level: str, use_tui: bool) -> str | None:
    """配置 loguru。TUI 模式下关闭 stderr 输出（否则会冲掉界面），改写日志文件。

    返回日志文件路径（无文件时为 None）。
    """
    logger.remove()

    log_dir = os.path.join(_script_dir, "btb_logs")
    log_file: str | None = None
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        logger.add(
            log_file,
            level="DEBUG",
            encoding="utf-8",
            rotation="10 MB",
            retention="7 days",
            enqueue=True,
        )
    except OSError:
        log_file = None

    if not use_tui:
        logger.add(sys.stderr, level=console_level, colorize=True)

    return log_file


def _run_with_tui(buyer, *, config_name: str, log_file: str | None) -> None:
    from util.log.TerminalRenderer import (
        TerminalRenderContext,
        create_terminal_renderer,
        render_message_stream,
    )

    renderer = create_terminal_renderer(
        TerminalRenderContext(
            config_name=config_name,
            log_file=log_file or "-",
            platform_name=os.name,
        ),
        prefer_rich=os.name == "nt",
    )
    render_message_stream(
        renderer,
        buyer.start_worker().iter_events(),
        on_message=logger.info,
    )


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    # 验证必要参数
    if not args.config_file and not args.tickets_info:
        parser.error("必须指定 --config-file 或 --tickets-info 其中一个")

    config = _build_config_from_args(args)
    resolved = config.resolved_config()

    # 显示模式：Windows 默认启用 Textual TUI（与主仓库一致），可用 --no-tui 关闭。
    # 非 tty（重定向/管道）时也回退到纯文本，避免破坏渲染。
    use_tui = (
        os.name == "nt"
        and not args.no_tui
        and sys.stdout is not None
        and sys.stdout.isatty()
    )

    log_level = str(args.log_level or "standard").lower()
    log_file = _setup_logging(
        console_level=_resolve_log_level(log_level),
        use_tui=use_tui,
    )

    logger.info("btb_cli 启动中...")
    logger.info(f"日志级别: {log_level} | 显示模式: {'Textual TUI' if use_tui else '纯文本'}")

    # 验证 tickets_info 内容
    try:
        ticket_data = json.loads(resolved.tickets_info)
        detail = ticket_data.get("detail", "未知")
        logger.info(f"活动: {detail}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"订单 JSON 解析失败: {e}")
        sys.exit(1)

    from core.buy import Buy

    config_name = os.path.basename(args.config_file) if args.config_file else "default"
    buyer = Buy(config=resolved)

    try:
        if use_tui:
            _run_with_tui(buyer, config_name=config_name, log_file=log_file)
        else:
            buyer.buy()
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"抢票过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
