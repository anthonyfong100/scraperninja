import asyncio
import logging
from typing import Callable, Iterable, List, Optional

from playwright.sync_api import Page, Request, Response
from pydantic import BaseModel
from scrapling.fetchers import AsyncStealthySession

from scraperninja.constants import (
    BASE_AMERICAN_AIRLINES_URL,
    MAIN_PAGE_CSS_SELECTOR,
    RESULT_GRID_CONTAINER_CLASS_SELECTOR,
    SEARCH_ITINERARY_URL,
)
from scraperninja.model.api.flight_search_response import FlightSearchResponse
from scraperninja.model.proxy_settings import proxySettings
from scraperninja.scraper.flight_search.base_flight_search_response_api import (
    BaseFlightSearchResponseApi,
)

NetworkRequestPredicate = Callable[[Request], bool]
NetworkResponsePredicate = Callable[[Response], bool]


class CamouFoxBrowserNetworkFlightSearchResponseApi(BaseFlightSearchResponseApi):
    """
    American Airlines browser network scraper implementation for flight search
    responses. Uses StealthySession and PageNetworkSpy to capture flight data.
    """

    def __init__(self, proxy_url: Optional[str] = None) -> None:
        self.network_spy = PageNetworkSpy(
            req_predicates=[searchItineraryFilter],
            res_predicates=[searchItineraryFilter],
        )
        self.session = AsyncStealthySession(
            page_action=self.network_spy.spy,
            humanize=True,
            os_randomize=True,
            google_search=True,
            geoip=proxySettings.should_use_proxy,
            headless=False,
            proxy=proxy_url,
        )
        self.cache = {}

    async def __aenter__(self):
        await self.session.__aenter__()
        await self._warm_up_session()
        return self

    async def __aexit__(self, _exc_type, _exc_value, _traceback):
        await self.session.__aexit__(_exc_type, _exc_value, _traceback)
        return False

    async def _warm_up_session(self):
        """Pre-warm the session by visiting AA homepage to establish proper context."""
        logging.info("Warming up session with AA homepage")
        try:
            await self.session.fetch(
                BASE_AMERICAN_AIRLINES_URL,
                wait_selector=MAIN_PAGE_CSS_SELECTOR,
            )
        except Exception as e:
            logging.warning(f"Session warm-up failed, continuing anyway: {e}")

    async def search_flight_details(
        self,
        search_url: str,
        direct_only: bool,
    ) -> List[FlightSearchResponse]:
        if (search_url, direct_only) in self.cache:
            return self.cache[(search_url, direct_only)]
        logging.info(f"Fetching search URL: {search_url}")
        # We need to clear here since we are spying multiple times in the same session
        # and it does not automatically clear
        self.network_spy.clear()
        logging.info("Waiting for result grid results to appear")
        await self.session.fetch(
            search_url,
            wait_selector=RESULT_GRID_CONTAINER_CLASS_SELECTOR,
        )

        if not self.network_spy.responses:
            raise ValueError("No responses captured by PageNetworkSpy")

        logging.info("Flight search completed. Processing captured responses...")

        all_flight_details_during_day_response = self.network_spy.responses[
            0
        ].json_payload
        all_flight_information_during_day = [
            FlightSearchResponse.model_validate(slice_dict)
            for slice_dict in all_flight_details_during_day_response["slices"]
        ]

        if direct_only:
            return [
                flight
                for flight in all_flight_information_during_day
                if flight.is_direct_flight
            ]

        self.cache[(search_url, direct_only)] = all_flight_information_during_day
        return all_flight_information_during_day


class NetworkSpiedRequest(BaseModel):
    url: str
    method: str
    body: Optional[dict] = None


class NetworkSpiedResponse(BaseModel):
    url: str
    status: int
    json_payload: dict


class PageNetworkSpy:
    logger = logging.getLogger(f"{__name__}")

    def __init__(
        self,
        req_predicates: Iterable[NetworkRequestPredicate] = [],
        res_predicates: Iterable[NetworkResponsePredicate] = [],
    ) -> None:
        self.requests: list[NetworkSpiedRequest] = []
        self.responses: list[NetworkSpiedResponse] = []
        self.req_predicates = req_predicates
        self.res_predicates = res_predicates

    async def spy(self, page: Page):
        def handle_response_sync(response: Response) -> None:
            asyncio.create_task(self.__handle_response(response))

        page.on("request", self.__handle_request)
        page.on("response", handle_response_sync)

    def debug_print(self):
        self.logger.debug("############# Network requests #############")
        for req in self.requests:
            self.logger.debug(req)

        self.logger.debug("############# Network response #############")
        for res in self.responses:
            self.logger.debug(res)

    def __handle_request(self, request: Request):
        should_keep = all([predicate(request) for predicate in self.req_predicates])
        if not should_keep:
            self.logger.debug(
                f"Request url {request.url}, Request method {request.method}"
                "has been skipped"
            )
            return

        self.requests.append(
            NetworkSpiedRequest(
                url=request.url,
                method=request.method,
                body=request.post_data_json,
            )
        )

    async def __handle_response(self, response: Response):
        should_keep = all([predicate(response) for predicate in self.res_predicates])
        if not should_keep:
            self.logger.debug(
                f"Request url {response.url}, Request method {response.status} "
                "has been skipped"
            )
            return

        self.responses.append(
            NetworkSpiedResponse(
                url=response.url,
                status=response.status,
                json_payload=await response.json(),
            )
        )

    def clear(self):
        self.requests.clear()
        self.responses.clear()


def searchItineraryFilter(req: Request | Response):
    return req.url == SEARCH_ITINERARY_URL
