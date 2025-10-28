from pydantic import BaseModel


class Money(BaseModel):
    amount: float
    currency: str

    @staticmethod
    def empty() -> "Money":
        return Money(amount=0.0, currency="USD")

    def safe_get_amount(self, expected_currency="USD") -> float:
        if self.currency == expected_currency:
            return self.amount
        raise NotImplementedError("Currency conversion not implemented")

    # TODO: Implement currency conversion if needed
    def check_same_currency(self, other: "Money"):
        if self.currency != other.currency:
            raise ValueError("Money operations require the same currency")
