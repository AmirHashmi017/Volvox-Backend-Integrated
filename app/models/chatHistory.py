from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional,List
from datetime import datetime, timezone

class Message(BaseModel):
    question: str
    response: str
    research_id: Optional[str] = Field(alias="research_id", default=None)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("research_id", mode="before")
    @classmethod
    def _objectid_to_str(cls, v):
        if v is None:
            return v
        return str(v)

class chatHistoryModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: Optional[str] = Field(alias="user_id", default=None)
    title: str

    messages: List[Message] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", "userId", mode="before")
    @classmethod
    def _objectid_to_str(cls, v):
        if v is None:
            return v
        return str(v)
