from typing import Optional

from pydantic import BaseModel

from scraperninja.model.api.flight_search_response import ProductType


class AnalysisParams(BaseModel):
    origin: str
    destination: str
    date: str
    passengers: int
    cabin_class: ProductType
    output_file_path: Optional[str] = None
    debug: bool
    direct_only: bool
    use_camoufox_browser: bool
