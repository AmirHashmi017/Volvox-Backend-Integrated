from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
