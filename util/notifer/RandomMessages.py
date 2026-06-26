import random

FAIL_MESSAGES = [
    "再接再厉！",
    "没事的，运气下次会好！",
    "加油加油！",
    "继续冲！",
    "坚持就是胜利！",
]


def get_random_fail_message() -> str:
    return random.choice(FAIL_MESSAGES)
