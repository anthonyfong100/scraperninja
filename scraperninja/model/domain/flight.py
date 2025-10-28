from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from scraperninja.constants import TIME_FORMAT_HH_MM
from scraperninja.model.money import Money


class FlightTiming(BaseModel):
    flight_number: str
    departure_time: datetime
    arrival_time: datetime


class FlightCashPrice(BaseModel):
    price: Money


class FlightMilesPrice(BaseModel):
    points_required: Optional[int]
    tax: Money


class FlightTimingAndPrices(FlightTiming, FlightCashPrice, FlightMilesPrice):
    @property
    def cpp(self) -> Optional[float]:
        """Calculate the cents per point (CPP) value for the flight."""
        if not self.points_required or self.points_required == 0:
            return None
        self.price.check_same_currency(self.tax)
        return (self.price.amount - self.tax.amount) * 100 / self.points_required

    def to_report(self):
        return {
            "flight_number": self.flight_number,
            "departure_time": self.departure_time.strftime(TIME_FORMAT_HH_MM),
            "arrival_time": self.arrival_time.strftime(TIME_FORMAT_HH_MM),
            "points_required": self.points_required,
            "cash_price_usd": self.price.safe_get_amount(expected_currency="USD"),
            "taxes_fees_usd": self.tax.safe_get_amount(expected_currency="USD"),
            "cpp": self.cpp if self.cpp else None,
        }
