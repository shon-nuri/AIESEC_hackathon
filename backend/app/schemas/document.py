from datetime import date, datetime
from typing import List
from pydantic import BaseModel, ConfigDict
from backend.app.enums import Status, Label
from backend.app.schemas.page import PageWithDetections


class DocumentOut(BaseModel):
    id: int
    filename: str 
    mime_type: str
    pages_count: int
    uploaded_at: datetime
    status: Status

    model_config = ConfigDict(from_attributes=True)


class DocumentWithPages(DocumentOut):
    pages: List[PageWithDetections]