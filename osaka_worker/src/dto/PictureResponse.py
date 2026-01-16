from pydantic import BaseModel, Field

class PictureResponse(BaseModel):
    s3_url: str = Field(...)
    request_id: str