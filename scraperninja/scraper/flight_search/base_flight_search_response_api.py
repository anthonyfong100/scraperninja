from abc import ABC, abstractmethod
from typing import List

from scraperninja.model.api.flight_search_response import FlightSearchResponse


class BaseFlightSearchResponseApi(ABC):
    @abstractmethod
    async def search_flight_details(
        self,
        search_url: str,
        direct_only: bool,
    ) -> List["FlightSearchResponse"]:
        pass
