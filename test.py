from pydantic import BaseModel, Field
from typing import Optional



class A(BaseModel):
    _id: Optional[str] = Field(default=None, alias="id")
    status: str

    class Config:
        allow_population_by_field_name = True



a = A(_id='213123123', status="ok")
print(a)
print(a.dict(by_alias=True))


