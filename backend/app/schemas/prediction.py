from typing import List
from pydantic import BaseModel

from backend.app.schemas.page import PageWithDetections


class PredictionOut(BaseModel):
    document_id: id
    pages: List[PageWithDetections]