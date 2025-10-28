"""Models for American Airlines flight slice response data."""

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel

from scraperninja.model.domain.flight import (
    FlightCashPrice,
    FlightMilesPrice,
    FlightTiming,
)
from scraperninja.model.money import Money


class ProductGroup(Enum):
    MAIN = "MAIN"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    PREMIUM = "PREMIUM"


class ProductType(Enum):
    BASIC_ECONOMY = "BASIC_ECONOMY"
    COACH = "COACH"
    COACH_PLUS = "COACH_PLUS"
    COACH_SELECT = "COACH_SELECT"
    COACH_FLEXIBLE = "COACH_FLEXIBLE"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    PREMIUM_ECONOMY_FLEXIBLE = "PREMIUM_ECONOMY_FLEXIBLE"
    BUSINESS = "BUSINESS"
    BUSINESS_FLEXIBLE = "BUSINESS_FLEXIBLE"
    FIRST = "FIRST"
    FIRST_FLEXIBLE = "FIRST_FLEXIBLE"


class Airport(BaseModel):
    city: str
    cityName: str
    code: str
    countryCode: str
    domestic: bool
    name: str
    stateCode: str


class Aircraft(BaseModel):
    code: str
    name: str
    shortName: str


class Flight(BaseModel):
    carrierCode: str
    carrierName: str
    flightNumber: str

    @property
    def flight_number_with_carrier_code(self) -> str:
        return f"{self.carrierCode}{self.flightNumber}"


class Surcharge(BaseModel):
    code: str
    price: Money


class ProductDetail(BaseModel):
    alerts: List[Any] = []
    basicEconomyPlus: bool
    bookingCode: str
    businessPlus: bool
    cabinType: str
    flagship: bool
    flagshipSuite: bool
    hash: Optional[str] = None
    meals: List[str]
    productType: ProductType
    upgradeable: bool
    webSpecial: bool


class Leg(BaseModel):
    aircraft: Aircraft
    aircraftCode: str
    alerts: List[Any] = []
    amenities: List[str] = []
    arrivalDateTime: str
    arrivesNextDay: int
    brazilian: bool
    brazilOnTimePerformance: Optional[Any] = None
    connectionTimeInMinutes: int
    departureDateTime: str
    destination: Airport
    distanceInMiles: int
    domestic: bool
    durationInMinutes: int
    flight: Optional[Flight] = None
    operationalDisclosure: str
    origin: Airport
    productDetails: List[ProductDetail]


class Fare(BaseModel):
    accountCodes: List[Any] = []
    dynamicFare: bool
    endorsements: List[Any] = []
    surcharges: List[Surcharge]


class Segment(BaseModel):
    alerts: List[Any] = []
    arrivalDateTime: str
    changeOfGauge: bool
    departureDateTime: str
    destination: Airport
    fares: List[Any] = []
    flight: Flight
    legs: List[Leg]
    marriedSegmentIndex: Optional[int] = None
    origin: Airport
    throughFlight: bool


class SlicePricing(BaseModel):
    allPassengerDisplayFareTotal: Money
    allPassengerDisplayTaxTotal: Money
    allPassengerDisplayTotal: Money
    perPassengerAwardPoints: str


class RefundableProduct(BaseModel):
    corporateFare: bool
    indicator: str
    jsonKey: str
    productType: ProductType
    refundAmount: Money
    solutionID: str
    totalAmount: Money
    travelPolicy: Optional[Any] = None


class PricingDetail(BaseModel):
    allPassengerDisplayTotal: Optional[Money] = None
    allPassengerTaxesAndFees: Optional[Money] = None
    basicEconomyPlus: bool
    benefitKey: str
    businessPlus: bool
    corporateFare: bool
    dynamicFare: bool
    extendedFareCode: str
    fareCardTag: Optional[str] = None
    fares: List[Fare]
    flagship: bool
    flagshipRiskyConnection: bool
    flagshipSuite: bool
    flexible: bool
    hash: Optional[str] = None
    lieFlat: bool
    lowestPriceForProductGroup: bool
    mustBookAtAirport: bool
    perPassengerAwardPoints: int
    perPassengerDisplayTotal: Money
    perPassengerTaxesAndFees: Money
    productAvailable: bool
    productBenefits: str
    productGroup: Optional[ProductGroup] = None
    productType: ProductType
    refundableProducts: List[RefundableProduct]
    seatsRemaining: int
    slicePricing: Optional[SlicePricing] = None
    solutionID: Optional[str] = None
    tripType: str
    webSpecial: bool

    def __lt__(self, other: "PricingDetail") -> bool:
        self_slice_pricing = (
            self.slicePricing.allPassengerDisplayTotal
            if self.slicePricing
            else Money.empty()
        )

        other_slice_pricing = (
            other.slicePricing.allPassengerDisplayTotal
            if other.slicePricing
            else Money.empty()
        )

        return self_slice_pricing.amount < other_slice_pricing.amount


class ProductPricing(BaseModel):
    cheapestPrice: PricingDetail
    regularPrice: PricingDetail
    webSpecialPrice: Optional[PricingDetail] = None


class FlightSearchResponse(BaseModel):
    arrivalDateTime: str
    departureDateTime: str
    destination: Airport
    durationInMinutes: int
    hash: str
    origin: Airport
    pricingDetail: List[PricingDetail] = []
    productPricing: List[ProductPricing] = []
    segments: List[Segment] = []

    @property
    def all_flight_numbers_str(self) -> str:
        return "_".join(
            [
                segment.flight.flight_number_with_carrier_code
                for segment in self.segments
            ]
        )

    @property
    def is_direct_flight(self) -> bool:
        return len(self.segments) == 1

    def get_cheapest_cash_price(
        self, product_type: ProductType
    ) -> Optional[FlightCashPrice]:
        relevantPricingDetails = [
            pricingDetail
            for pricingDetail in self.pricingDetail
            if pricingDetail.productType == product_type
        ]
        sorted_prices = sorted(relevantPricingDetails)
        cheapest_price = sorted_prices[0].slicePricing if sorted_prices else None

        if not cheapest_price:
            return None

        return FlightCashPrice(
            price=cheapest_price.allPassengerDisplayTotal,
        )

    def get_flight_timing(self) -> Optional[FlightTiming]:
        if not self.segments:
            return None

        # TODO: Handle multi-segment flights
        segment = self.segments[0]
        return FlightTiming.model_validate(
            {
                "flight_number": segment.flight.flight_number_with_carrier_code,
                "departure_time": segment.departureDateTime,
                "arrival_time": segment.arrivalDateTime,
            }
        )

    def get_miles_required(
        self, product_type: ProductType
    ) -> Optional[FlightMilesPrice]:
        relevantPricingDetails = [
            pricingDetail
            for pricingDetail in self.pricingDetail
            if pricingDetail.productType == product_type
        ]
        sorted_prices = sorted(relevantPricingDetails)
        cheapest_price = sorted_prices[0] if sorted_prices else None

        if not cheapest_price:
            return None

        return FlightMilesPrice(
            points_required=cheapest_price.perPassengerAwardPoints,
            tax=cheapest_price.perPassengerTaxesAndFees,
        )
