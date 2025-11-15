from pydantic import BaseModel, ConfigDict
from app.enums import Status, Label


class DetectionBase(BaseModel):
    label: Label
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float


class DetectionOut(DetectionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)