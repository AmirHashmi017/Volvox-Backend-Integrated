from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime, timezone

class createResearch(BaseModel):
    researchName: str 
    fileName: str
    extension: str
    bytes: Optional[int] = None


class ResearchResponse(BaseModel):
    id: str = Field(alias="_id")
    userId: str = Field(alias="user_id")
    researchName: str
    fileName: str
    extension: str
    fileId: Optional[str] = Field(alias="file_id", default=None)
    createdAt: datetime
    fileUrl: Optional[str] = None

    class Config:
        populate_by_name = True

    @field_serializer("createdAt")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace('+00:00', 'Z')
