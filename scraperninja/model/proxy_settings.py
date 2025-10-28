from typing import Optional

from pydantic_settings import BaseSettings


class ProxySettings(BaseSettings):
    PROXY_URLS: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def proxy_urls_list(self) -> list[str]:
        if self.PROXY_URLS is None:
            return []
        return [url.strip() for url in self.PROXY_URLS.split(",") if url.strip()]

    @property
    def should_use_proxy(self) -> bool:
        return len(self.proxy_urls_list) > 0


proxySettings = ProxySettings()
