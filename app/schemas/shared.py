from pydantic import BaseModel, ConfigDict


class BaseRead(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)
