from typing import Any, Optional

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    id: str
    filename: str
    status: str
    file_path: str
    vision_file_path: Optional[str]
    summary: Optional[Any] = None
    result: Optional[dict] = None

    class Config:
        from_attributes = True
