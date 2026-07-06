"""Sonification schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class DataPoint(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    value: float = Field(...)


class SonifyRequest(BaseModel):
    data_points: list[DataPoint] = Field(..., min_length=1, max_length=50)
    chart_type: str = Field(default="bar", pattern="^(bar|line|pie)$")


class ToneInfo(BaseModel):
    label: str
    value: float
    frequency: float
    duration: float


class SonifyResponse(BaseModel):
    success: bool = True
    message: str = "Sonification thành công"
    data: Optional[dict] = None
