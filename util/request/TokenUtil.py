import base64
import time


_BASE64_STD_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/+="
)
_BASE64_TOKEN_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-."
)


def generate_token(
    project_id: int,
    screen_id: int,
    order_type: int,
    count: int,
    sku_id: int,
    ts: int | None = None,
) -> str:
    timestamp = int(time.time()) if ts is None else int(ts)
    token = bytes([0xC0])
    token += timestamp.to_bytes(4, "big")
    token += int(project_id).to_bytes(4, "big")
    token += int(screen_id).to_bytes(4, "big")
    token += int(order_type).to_bytes(1, "big")
    token += int(count).to_bytes(2, "big")
    token += int(sku_id).to_bytes(4, "big")

    encoded = base64.b64encode(token).decode("ascii")
    return encoded.translate(
        str.maketrans(_BASE64_STD_ALPHABET, _BASE64_TOKEN_ALPHABET)
    )
