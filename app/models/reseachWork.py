from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from typing import Optional
from datetime import datetime, timezone

class ResearchModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)

    userId: Optional[str] = Field(alias="user_id", default=None)

    researchName: str
    fileName: str
    extension: str
    fileId: Optional[str] = Field(alias="file_id", default=None)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", "userId", "fileId", mode="before")
    @classmethod
    def _objectid_to_str(cls, v):
        if v is None:
            return v
        return str(v)

    @field_validator("createdAt", mode="before")
    @classmethod
    def ensure_utc_timezone(cls, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            else:
                return v.astimezone(timezone.utc)
        return v

    @field_serializer("createdAt")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace('+00:00', 'Z')
