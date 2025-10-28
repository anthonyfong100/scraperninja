import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ProxyManager:
    logger = logging.getLogger(f"{__name__}")
    NO_PROXY_DUMMY_URL = "NO_PROXY"

    def __init__(
        self,
        proxy_urls: List[str],
        prefer_no_proxy: bool = True,
        default_block_duration_seconds: int = 60 * 10,
    ):
        self.all_available_proxy_urls = proxy_urls
        self.proxy_blocked_til: Dict[str, datetime] = {}
        self.prefer_no_proxy = prefer_no_proxy
        self.default_block_duration_seconds = default_block_duration_seconds

    def get_proxy(self) -> Optional[str]:
        proxy_list = (
            [self.NO_PROXY_DUMMY_URL] + self.all_available_proxy_urls
            if self.prefer_no_proxy
            else self.all_available_proxy_urls + [self.NO_PROXY_DUMMY_URL]
        )

        for proxy in proxy_list:
            if proxy not in self.proxy_blocked_til:
                self.logger.info(f"Found unblocked proxy: {proxy}")
                return self.__safe_return_proxy_url(proxy)
            if datetime.now() >= self.proxy_blocked_til[proxy]:
                del self.proxy_blocked_til[proxy]
                self.logger.info(f"Unblocking proxy: {proxy}")
                return self.__safe_return_proxy_url(proxy)
        return None

    def __safe_return_proxy_url(self, proxy_url: str) -> Optional[str]:
        if proxy_url == self.NO_PROXY_DUMMY_URL:
            return None
        return proxy_url

    def block_proxy_for_duration(
        self,
        proxy_url: Optional[str],
        seconds: Optional[int] = None,
    ) -> None:
        block_seconds = (
            seconds if seconds is not None else self.default_block_duration_seconds
        )
        proxy_url_safe = self.NO_PROXY_DUMMY_URL if proxy_url is None else proxy_url
        unblock_time = datetime.now() + timedelta(seconds=block_seconds)
        self.proxy_blocked_til[proxy_url_safe] = unblock_time
