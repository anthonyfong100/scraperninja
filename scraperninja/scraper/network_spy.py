import logging
from typing import Callable, Iterable, Optional

from playwright.sync_api import Page, Request, Response
from pydantic import BaseModel

from scraperninja.constants import SEARCH_ITINERARY_URL

NetworkRequestPredicate = Callable[[Request], bool]
NetworkResponsePredicate = Callable[[Response], bool]


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

    def spy(self, page: Page):
        page.on("request", self.__handle_request)
        page.on("response", self.__handle_response)

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

    def __handle_response(self, response: Response):
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
                json_payload=response.json(),
            )
        )

    def clear(self):
        self.requests.clear()
        self.responses.clear()


def searchItineraryFilter(req: Request | Response):
    return req.url == SEARCH_ITINERARY_URL
