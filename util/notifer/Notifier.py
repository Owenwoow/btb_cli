from abc import ABC, abstractmethod
import threading
import loguru
import time

from config.NotifierConfig import NotifierConfig


class NotifierBase(ABC):
    """推送器基类。

    daemon=True 是为了不阻塞进程，但 CLI 模式下需要在成功后手动 join_all
    等待所有推送线程真正完成，否则主进程退出会杀死 daemon 线程。
    """

    def __init__(
        self,
        title: str,
        content: str,
        interval_seconds=10,
        duration_minutes=10,
    ):
        super().__init__()
        self.title = title
        self.content = content
        self.interval_seconds = interval_seconds
        self.duration_minutes = duration_minutes
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        """线程运行函数，实现间隔发送通知"""
        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        count = 0

        while time.time() < end_time and not self.stop_event.is_set():
            try:
                remaining_minutes = int((end_time - time.time()) / 60)
                remaining_seconds = int((end_time - time.time()) % 60)
                message = f"{self.content} [#{count}, 剩余 {remaining_minutes}分{remaining_seconds}秒]"
                self.send_message(self.title, message)
                break
            except Exception as e:
                loguru.logger.error(f"通知发送失败: {e}")
                time.sleep(self.interval_seconds)

        loguru.logger.info("通知发送成功")

    def start(self):
        if not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=3)

    @abstractmethod
    def send_message(self, title, message):
        """用于发送消息，子类必须实现此方法"""
        pass


class NotifierManager:
    def __init__(self):
        self.notifier_dict: dict[str, NotifierBase] = {}

    def register_notifier(self, name: str, notifier: NotifierBase):
        if name in self.notifier_dict:
            loguru.logger.error(f"推送器添加失败: 已存在名为{name}的推送器")
        else:
            self.notifier_dict[name] = notifier
            loguru.logger.info(f"成功添加推送器: {name}")

    def remove_notifier(self, name: str):
        if name not in self.notifier_dict:
            loguru.logger.error(f"推送器删除失败: 不存在名为{name}的推送器")
        else:
            self.notifier_dict.pop(name)
            loguru.logger.info(f"成功删除推送器: {name}")

    def start_all(self):
        for notifer in self.notifier_dict.values():
            notifer.start()

    def stop_all(self):
        for notifer in self.notifier_dict.values():
            notifer.stop()

    def join_all(self, timeout: float = 30) -> None:
        """等待所有推送线程完成。
        
        [BUG FIX #977] CLI 模式下，推送线程是 daemon=True，
        主进程在 buy_stream 结束后若直接退出，daemon 线程被强制杀死，
        导致通知未能发出。调用此方法可阻塞等待所有推送线程实际完成。
        """
        for notifier in self.notifier_dict.values():
            if notifier.thread.is_alive():
                notifier.thread.join(timeout=timeout)

    def start_notifier(self, name: str):
        notifer = self.notifier_dict.get(name)
        if notifer:
            notifer.start()
        else:
            loguru.logger.error(f"推送器启动失败: 不存在名为{name}的推送器")

    def stop_notifier(self, name: str):
        notifer = self.notifier_dict.get(name)
        if notifer:
            notifer.stop()
        else:
            loguru.logger.error(f"推送器停止失败: 不存在名为{name}的推送器")

    def list_notifiers(self):
        return list(self.notifier_dict.keys())

    @staticmethod
    def create_from_config(
        config: NotifierConfig,
        title: str,
        content: str,
        interval_seconds: int = 10,
        duration_minutes: int = 10,
        include_audio: bool = True,
    ) -> "NotifierManager":
        manager = NotifierManager()

        if config.serverchan_key:
            try:
                from util.notifer.ServerChanUtil import ServerChanTurboNotifier
                notifier = ServerChanTurboNotifier(
                    token=config.serverchan_key, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("ServerChanTurbo", notifier)
            except Exception as e:
                loguru.logger.error(f"ServerChanTurbo创建失败: {e}")

        if config.serverchan3_api_url:
            try:
                from util.notifer.ServerChanUtil import ServerChan3Notifier
                notifier = ServerChan3Notifier(
                    api_url=config.serverchan3_api_url, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("ServerChan3", notifier)
            except Exception as e:
                loguru.logger.error(f"ServerChan3创建失败: {e}")

        if config.pushplus_token:
            try:
                from util.proxy.PushPlusUtil import PushPlusNotifier
                notifier = PushPlusNotifier(
                    token=config.pushplus_token, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("PushPlus", notifier)
            except Exception as e:
                loguru.logger.error(f"PushPlus创建失败: {e}")

        if config.bark_token:
            try:
                from util.notifer.BarkUtil import BarkNotifier
                notifier = BarkNotifier(
                    token=config.bark_token, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("Bark", notifier)
            except Exception as e:
                loguru.logger.error(f"Bark创建失败: {e}")

        if config.ntfy_url:
            try:
                from util.notifer.NtfyUtil import NtfyNotifier
                notifier = NtfyNotifier(
                    url=config.ntfy_url, username=config.ntfy_username,
                    password=config.ntfy_password, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("Ntfy", notifier)
            except Exception as e:
                loguru.logger.error(f"Ntfy创建失败: {e}")

        if config.meow_nickname:
            try:
                from util.notifer.MeoWUtil import MeoWNotifier
                notifier = MeoWNotifier(
                    nickname=config.meow_nickname, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("MeoW", notifier)
            except Exception as e:
                loguru.logger.error(f"MeoW创建失败: {e}")

        if include_audio and config.audio_path:
            try:
                from util.notifer.AudioUtil import AudioNotifier
                notifier = AudioNotifier(
                    audio_path=config.audio_path, title=title, content=content,
                    interval_seconds=interval_seconds, duration_minutes=duration_minutes,
                )
                manager.register_notifier("Audio", notifier)
            except Exception as e:
                loguru.logger.error(f"Audio创建失败: {e}")

        return manager
