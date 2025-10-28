import argparse
import asyncio
import json
import logging
from typing import List, Optional

from tenacity import Retrying, stop_after_attempt, wait_exponential

from scraperninja.model.analysis_params import AnalysisParams
from scraperninja.model.api.flight_search_request import (
    FlightSearchRequest,
    PaymentType,
)
from scraperninja.model.domain.flight import FlightTimingAndPrices
from scraperninja.model.proxy_settings import proxySettings
from scraperninja.scraper.american_airline_flight_scraper import (
    AmericanAirlineFlightScraper,
)
from scraperninja.scraper.flight_search import (
    CamouFoxBrowserNetworkFlightSearchResponseApi,
    ChromeBrowserNetworkFlightSearchResponseApi,
)
from scraperninja.scraper.proxy_manager import ProxyManager


async def run_cent_per_mile_analysis_with_retries(
    params: AnalysisParams,
    proxy_manager: ProxyManager,
):
    try:
        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=5, max=60),
        ):
            proxy_url = proxy_manager.get_proxy()
            with attempt:
                try:
                    return await _run_cent_per_mile_analysis(params, proxy_url)
                except Exception as e:
                    logging.error(f"Error during analysis with proxy {proxy_url}: {e}")
                    proxy_manager.block_proxy_for_duration(proxy_url)
                    raise e
    except Exception as final_exception:
        logging.critical(f"All retries failed: {final_exception}")
        raise final_exception
    return []


async def _run_cent_per_mile_analysis(
    params: AnalysisParams,
    proxy_url: Optional[str],
):
    flight_api = (
        CamouFoxBrowserNetworkFlightSearchResponseApi(proxy_url)
        if params.use_camoufox_browser
        else ChromeBrowserNetworkFlightSearchResponseApi(proxy_url)
    )
    async with flight_api as flightResponseApi:
        scraper = AmericanAirlineFlightScraper(flightResponseApi)

        cash_search_req = FlightSearchRequest(
            orig=params.origin,
            dest=params.destination,
            date=params.date,
            adult=params.passengers,
            search_type=PaymentType.REVENUE,
        )

        logging.info(f"Searching flights timings: {cash_search_req}")
        flight_timings = await scraper.scrape_flight_timing(
            cash_search_req,
            direct_only=params.direct_only,
        )
        logging.info(f"Searching flights prices: {cash_search_req}")
        flight_cash_prices = await scraper.scrape_cash_prices(
            cash_search_req,
            product_type=params.cabin_class,
            direct_only=params.direct_only,
        )

        miles_search_req = FlightSearchRequest(
            orig=params.origin,
            dest=params.destination,
            date=params.date,
            adult=params.passengers,
            search_type=PaymentType.AWARD,
        )

        logging.info(f"Searching flights miles redemption: {miles_search_req}")
        flight_miles_prices = await scraper.scrape_miles_prices(
            miles_search_req,
            product_type=params.cabin_class,
            direct_only=params.direct_only,
        )
        all_flight_prices: List[FlightTimingAndPrices] = []

    for flight_number in flight_timings.keys():
        flight_timing = flight_timings.get(flight_number)
        cash_price = flight_cash_prices.get(flight_number)
        mile_price = flight_miles_prices.get(flight_number)
        if not flight_timing or not cash_price or not mile_price:
            logging.warning(
                f"Skipping flight {flight_number} due to missing data: "
                f"timing={flight_timing}, cash_price={cash_price}, "
                f"mile_price={mile_price}"
            )
            continue

        all_flight_prices.append(
            FlightTimingAndPrices.model_validate(
                {
                    **flight_timing.model_dump(),
                    **cash_price.model_dump(),
                    **mile_price.model_dump(),
                }
            )
        )

    return all_flight_prices


def report_results(
    params: AnalysisParams,
    flight_prices: List[FlightTimingAndPrices],
    output_file_path: Optional[str] = None,
):
    flights_formatted = [flight.to_report() for flight in flight_prices]
    formatted_json = {
        "search_metadata": {
            "origin": params.origin,
            "destination": params.destination,
            "date": params.date,
            "passengers": params.passengers,
            "cabin_class": params.cabin_class.value,
        },
        "flights": flights_formatted,
        "total_results": len(flight_prices),
    }

    logging.info("\n##### SCRAPER RESULTS #####")
    logging.info(f"Found {len(flight_prices)} flights")
    if output_file_path:
        logging.info(f"Writing results to {output_file_path}")
        with open(output_file_path, "w") as f:
            json.dump(formatted_json, f, indent=4, default=str)
    else:
        logging.info(f"Results: {formatted_json}")
    logging.info("\n##### SCRAPER RESULTS END #####")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run flight analysis for cent per mile calculations"
    )
    parser.add_argument(
        "--origin", "-o", required=True, help="Origin airport code (e.g., LAX)"
    )
    parser.add_argument(
        "-d",
        "--destination",
        required=True,
        help="Destination airport code (e.g., JFK)",
    )
    parser.add_argument(
        "--date", required=True, help="Flight date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--passengers",
        "-p",
        type=int,
        default=1,
        help="Number of passengers (default: 1)",
    )
    parser.add_argument(
        "--cabin-class",
        "-c",
        choices=["COACH", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
        default="COACH",
        help="Cabin class (default: COACH)",
    )
    parser.add_argument(
        "-f",
        "--output-file-path",
        help="Output file path (optional, defaults to logging)",
    )
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Verbose debug output",
    )
    parser.add_argument(
        "--direct-only",
        default=False,
        action="store_true",
        help="Only include direct flights in the results",
    )
    parser.add_argument(
        "--use-camoufox-browser",
        default=False,
        action="store_true",
        help="Use CamouFox browser for scraping",
    )

    params = AnalysisParams.model_validate(vars(parser.parse_args()))

    logging.basicConfig(
        level=logging.DEBUG if params.debug else logging.INFO,
    )

    if proxySettings.should_use_proxy:
        logging.info(f"All available proxies: {proxySettings.proxy_urls_list}")

    proxy_manager = ProxyManager(proxySettings.proxy_urls_list)

    results = asyncio.run(
        run_cent_per_mile_analysis_with_retries(params, proxy_manager)
    )
    report_results(params, results, output_file_path=params.output_file_path)
