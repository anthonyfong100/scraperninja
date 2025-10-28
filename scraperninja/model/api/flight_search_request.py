import json
from enum import Enum
from typing import List
from urllib.parse import quote, urlencode

from pydantic import BaseModel


class PaymentType(Enum):
    REVENUE = "Revenue"
    AWARD = "Award"


class FlightSearchRequest(BaseModel):
    orig: str
    dest: str
    date: str
    adult: int
    search_type: PaymentType
    pax: int = 1
    trip_type: str = "OneWay"
    fare_type: str = "Lowest"
    locale: str = "en_US"
    cabin: str = ""
    carriers: str = "ALL"
    travel_type: str = "personal"
    allow_origin_nearby: bool = False
    allow_dest_nearby: bool = False

    def to_params(self) -> dict:
        return {
            "locale": self.locale,
            "fareType": self.fare_type,
            "pax": self.pax,
            "adult": self.adult,
            "type": self.trip_type,
            "searchType": self.search_type.value,
            "cabin": self.cabin,
            "carriers": self.carriers,
            "travelType": self.travel_type,
        }

    def slices(self) -> List[dict]:
        return [
            {
                "orig": self.orig,
                "origNearby": self.allow_origin_nearby,
                "dest": self.dest,
                "destNearby": self.allow_dest_nearby,
                "date": self.date,
            }
        ]

    def to_url(self, base_url) -> str:
        query = urlencode(self.to_params())
        slices_json = json.dumps(self.slices(), separators=(",", ":"))
        slices_quoted = quote(slices_json, safe="")
        return f"{base_url}?{query}&slices={slices_quoted}"
