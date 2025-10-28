from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

from scraperninja.model.api.flight_search_response import FlightSearchResponse


class BaseFlightSearchResponseApi(ABC):
    @abstractmethod
    @lru_cache
    async def search_flight_details(
        self,
        search_url: str,
        direct_only: bool,
    ) -> List["FlightSearchResponse"]:
        pass
