# btb_cli — B站抢票 CLI 独立版

从 [biliTickerBuy](https://github.com/mikumifa/biliTickerBuy) 项目中分离的**纯 CLI 抢票模块**，无需 Gradio / Web UI，可独立运行。

## 修复内容

| Bug | 问题 | 修复 |
|-----|------|------|
| [#977](https://github.com/mikumifa/biliTickerBuy/issues/977) | CLI 抢票成功后推送通知（Server酱/Bark等）丢失 | `notifierManager.join_all(timeout=30)` 等待通知线程完成后再退出 |
| [#963](https://github.com/mikumifa/biliTickerBuy/issues/963) | 429 限流后光速重试触发 412 IP 风控封禁 | 429 错误改为 `should_sleep_before_next_attempt = True`，和普通失败一样走间隔冷却 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备订单配置文件

订单 JSON 格式与原项目 `biliTickerBuy` 完全兼容，示例：

```json
{
    "detail": "演唱会名称 - A区",
    "count": 1,
    "screen_id": 123456,
    "project_id": 654321,
    "sku_id": 111111,
    "pay_money": 38000,
    "order_type": 1,
    "buyer_info": [
        {
            "name": "张三",
            "personal_id": "身份证号",
            "tel": "手机号",
            "id_card_front": "",
            "id_card_back": "",
            "is_default": true
        }
    ],
    "buyer": "张三",
    "tel": "手机号",
    "deliver_info": {
        "name": "",
        "tel": "",
        "addr_id": 0,
        "addr": ""
    },
    "cookies": [
        {"name": "SESSDATA", "value": "你的SESSDATA"},
        {"name": "bili_jct", "value": "你的bili_jct"},
        {"name": "DedeUserID", "value": "你的UID"}
    ]
}
```

### 3. 运行

```bash
# 立即开始抢票
python main.py --config-file 订单.json

# 定时抢票（2026-06-28 20:00 开抢）
python main.py --config-file 订单.json --time-start 2026-06-28T20:00:00

# 使用代理
python main.py --config-file 订单.json --https-proxys http://user:pass@1.2.3.4:7890

# 使用多个代理（自动轮换）
python main.py --config-file 订单.json --https-proxys "http://p1.com:7890,http://p2.com:7890"

# 抢票成功后发送 Bark 通知
python main.py --config-file 订单.json --notifier-config.bark-token YOUR_BARK_TOKEN

# 组合使用
python main.py --config-file 订单.json \
    --time-start 2026-06-28T20:00:00 \
    --interval 800 \
    --create-retry-limit 30 \
    --create-request-batch-size N \
    --notifier-config.serverchan-key YOUR_KEY \
	--no-show-qrcode \
    --log-level standard
```

## 所有参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--config-file PATH` | — | 订单 JSON 文件路径（必填） |
| `--time-start DATETIME` | 立即 | 开抢时间 `2026-06-28T20:00:00` |
| `--interval MS` | 1000 | 请求间隔（毫秒） |
| `--create-retry-limit N` | 20 | 每轮最大重试次数 |
| `--create-request-batch-size N` | 3 | 批量并发数 |
| `--https-proxys PROXY` | none | 代理地址（逗号分隔多个） |
| `--auto-open-payment-url` | 否 | 成功后自动打开支付链接 |
| `--no-show-qrcode` | 弹出 | 不弹出二维码窗口 |
| `--notifier-config.serverchan-key KEY` | — | Server酱 Turbo SendKey |
| `--notifier-config.bark-token TOKEN` | — | Bark Token 或自托管地址 |
| `--notifier-config.pushplus-token TOKEN` | — | PushPlus Token |
| `--notifier-config.ntfy-url URL` | — | ntfy Topic URL |
| `--notifier-config.meow-nickname NICK` | — | MeoW 昵称 |
| `--notifier-config.audio-path PATH` | — | 成功时播放的本地音频 |
| `--log-level LEVEL` | standard | `simple` / `standard` / `debug` |

## 目录结构

```
btb_cli/
├── main.py              ← CLI 入口
├── requirements.txt
├── cptoken/             ← ctoken 生成（反风控核心）
├── config/              ← 配置类
├── core/                ← 抢票核心逻辑（buy.py / buy_helpers.py / buy_types.py）
├── interface/           ← Bilibili API 封装（项目信息获取）
└── util/                ← 工具类（请求/代理/通知/时间）
    ├── notifer/         ← 推送通知（Server酱/Bark/PushPlus/Ntfy/MeoW/音频）
    ├── proxy/           ← 代理池管理
    └── request/         ← HTTP 请求层（BiliRequest / CookieManager）
```
