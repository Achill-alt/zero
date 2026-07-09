from pydantic import BaseModel


class SearchResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
