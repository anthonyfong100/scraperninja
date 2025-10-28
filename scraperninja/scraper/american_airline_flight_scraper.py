from typing import Dict

from scraperninja.constants import (
    BASE_AMERICAN_AIRLINES_URL,
)
from scraperninja.model.api.flight_search_request import FlightSearchRequest
from scraperninja.model.api.flight_search_response import (
    ProductType,
)
from scraperninja.model.domain.flight import (
    FlightCashPrice,
    FlightMilesPrice,
    FlightTiming,
)
from scraperninja.scraper.flight_search import BaseFlightSearchResponseApi


class AmericanAirlineFlightScraper:
    """
    Opens a browser session for American Airlines and records all network traffic to
    capture api calls to fetch flight details and prices.
    """

    def __init__(self, flight_api: BaseFlightSearchResponseApi) -> None:
        self.flight_api = flight_api

    @staticmethod
    def __resolve_search_url(req: FlightSearchRequest) -> str:
        return req.to_url(f"{BASE_AMERICAN_AIRLINES_URL}/booking/search")

    async def scrape_cash_prices(
        self,
        req: FlightSearchRequest,
        product_type: ProductType,
        direct_only: bool,
    ):
        flight_cash_price_by_flight_number: Dict[str, FlightCashPrice] = {}
        cash_flights_responses = await self.flight_api.search_flight_details(
            self.__resolve_search_url(req),
            direct_only=direct_only,
        )

        for flight in cash_flights_responses:
            flight_cash_price = flight.get_cheapest_cash_price(
                product_type=product_type,
            )
            if not flight_cash_price:
                continue
            flight_cash_price_by_flight_number[flight.all_flight_numbers_str] = (
                flight_cash_price
            )

        return flight_cash_price_by_flight_number

    async def scrape_miles_prices(
        self,
        req: FlightSearchRequest,
        product_type: ProductType,
        direct_only: bool,
    ):
        flight_miles_price_by_flight_number: Dict[str, FlightMilesPrice] = {}
        miles_flight_responses = await self.flight_api.search_flight_details(
            self.__resolve_search_url(req),
            direct_only=direct_only,
        )

        for flight in miles_flight_responses:
            flight_miles_required = flight.get_miles_required(
                product_type=product_type,
            )
            if flight_miles_required is None:
                continue
            flight_miles_price_by_flight_number[flight.all_flight_numbers_str] = (
                flight_miles_required
            )

        return flight_miles_price_by_flight_number

    async def scrape_flight_timing(
        self,
        req: FlightSearchRequest,
        direct_only: bool,
    ):
        flight_timing_by_flight_number: Dict[str, FlightTiming] = {}
        flight_responses = await self.flight_api.search_flight_details(
            self.__resolve_search_url(req),
            direct_only=direct_only,
        )

        for flight in flight_responses:
            flight_timing = flight.get_flight_timing()
            if not flight_timing:
                continue
            flight_timing_by_flight_number[flight.all_flight_numbers_str] = (
                flight_timing
            )

        return flight_timing_by_flight_number
