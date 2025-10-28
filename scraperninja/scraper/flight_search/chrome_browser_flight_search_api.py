import json
import logging
from typing import List, Optional

from selenium_driverless import webdriver
from selenium_driverless.scripts.network_interceptor import (
    InterceptedRequest,
    NetworkInterceptor,
    RequestPattern,
)

from scraperninja.constants import (
    DEFAULT_SEARCH_TIMEOUT_MILISECONDS,
    SEARCH_ITINERARY_URL,
)
from scraperninja.model.api.flight_search_response import FlightSearchResponse
from scraperninja.scraper.flight_search.base_flight_search_response_api import (
    BaseFlightSearchResponseApi,
)


class ChromeBrowserNetworkFlightSearchResponseApi(BaseFlightSearchResponseApi):
    """
    Chrome-based flight search API using selenium-driverless.
    Intercepts American Airlines network traffic to extract flight JSON responses.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, proxy_url: Optional[str] = None) -> None:
        self.proxy_url = proxy_url
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1280,720")
        self.cache = {}
        if proxy_url:
            self.options.add_argument(f"--proxy-server={proxy_url}")

    async def __aenter__(self):
        self.driver = await webdriver.Chrome(options=self.options).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.driver.__aexit__(exc_type, exc_val, exc_tb)

    async def _intercept_flights(self, search_url: str) -> List[dict]:
        response_data = []
        if search_url in self.cache:
            return self.cache[search_url]

        async def on_response(data: InterceptedRequest):
            if data.request.url == SEARCH_ITINERARY_URL:
                body_text = await data.body
                if not body_text:
                    return
                if isinstance(body_text, bytes):
                    body_text = body_text.decode("utf-8")
                response_data.append(json.loads(body_text))
                await data.continue_response()

        async with NetworkInterceptor(
            self.driver,
            on_response=on_response,
            on_request=lambda data: data.continue_request(),
            patterns=[RequestPattern.AnyResponse, RequestPattern.AnyRequest],
        ) as interceptor:
            await self.driver.get(
                search_url, wait_load=True, timeout=DEFAULT_SEARCH_TIMEOUT_MILISECONDS
            )
            # need to iterate to allow async callbacks to complete
            async for data in interceptor:
                if response_data:
                    break

        self.cache[search_url] = response_data
        return response_data

    async def search_flight_details(
        self, search_url: str, direct_only: bool
    ) -> List[FlightSearchResponse]:
        """Public synchronous wrapper around async interception logic."""
        response_data = await self._intercept_flights(search_url)

        all_flight_details_during_day_response = response_data[0]
        all_flights = [
            FlightSearchResponse.model_validate(slice_dict)
            for slice_dict in all_flight_details_during_day_response["slices"]
        ]

        if direct_only:
            all_flights = [f for f in all_flights if f.is_direct_flight]

        return all_flights
