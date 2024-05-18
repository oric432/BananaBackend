from typing import List
from pydantic import BaseModel
from datetime import datetime


class ClassificationResult(BaseModel):
    index: int
    label: str
    confidence: float


class ImageWithMetadata(BaseModel):
    url: str
    width: int
    height: int


class ImageWithClassification(BaseModel):
    date: datetime
    image: ImageWithMetadata
    classification: List[ClassificationResult]


class PaginatedImages(BaseModel):
    images: List[ImageWithMetadata]
