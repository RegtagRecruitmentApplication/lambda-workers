from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class PictureRequest(BaseModel):
    image_url: HttpUrl = Field(...)
    top_text: str = Field(..., min_length=1, max_length=100)
    bottom_text: Optional[str] = Field(None, max_length=100)