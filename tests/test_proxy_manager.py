import pytest

from scraperninja.scraper.proxy_manager import ProxyManager


class TestProxyManager:
    @pytest.fixture
    def proxy_manager(self):
        """Create a ProxyManager instance for testing."""
        return ProxyManager(["1", "2", "3"], prefer_no_proxy=True)

    def test_get_random_proxy_prefer_no_proxy(self, proxy_manager: ProxyManager):
        """Test prefer no proxy"""
        assert proxy_manager.get_proxy() is None
        assert proxy_manager.get_proxy() is None
        assert proxy_manager.get_proxy() is None
        assert proxy_manager.get_proxy() is None

    def test_get_random_proxy_returns_random(self, proxy_manager):
        """Test getting a random proxy from the pool."""
        assert proxy_manager.get_proxy() is None
        proxy_manager.block_proxy_for_duration(None)

        proxies_returned = []
        for _ in range(3):
            proxy = proxy_manager.get_proxy()
            proxies_returned.append(proxy)
            proxy_manager.block_proxy_for_duration(proxy)
        assert set(proxies_returned) == set(proxy_manager.all_available_proxy_urls)
