from typing import List
from pydantic import BaseModel, ConfigDict
from app.enums import Status, Label
from backend.app.schemas.detection import DetectionOut


class PageBase(BaseModel):
    page_index: int
    width: float | None = None
    height: float | None = None


class PageWithDetections(PageBase):
    id: int
    detections: List[DetectionOut]


    model_config = ConfigDict(from_attributes=True)