from pydantic import BaseModel
from typing import List

class SourceInfo(BaseModel):
    filename: str
    page: str
    excerpt: str

class QueryResponse(BaseModel):
    short_answer: str
    detailed_answer: str
    sources: List[SourceInfo]
