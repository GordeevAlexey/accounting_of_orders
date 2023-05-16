from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

#Заделы на будущее)

class OrderType(str, Enum):
    command = "Приказ"
    order = "Распоряжение"


class Status(str, Enum):
    completed = "Завершено"
    on_execution = "На исполнении"


class AbstractOrder(BaseModel):
    id: Optional[str] = Field(default=None)
    employee: list[str] = Field(default_factory=list)
    deadline: str
    status_code: Status = Field(default="На исполнении")
    comment: Optional[str] = None

    class Config:  
        use_enum_values = True

    def to_db(self):
        row = self.dict()
        del row['id']
        return row


class Order(AbstractOrder):
    issue_idx: str
    issue_type: OrderType
    approving_date: str
    title: str
    initiator: list[str] = Field(default_factory=list)
    approving_employee: list[str] = Field(default_factory=list)
    reference: Optional[str] = None


class Suborder(AbstractOrder):
    id_orders: str
    content: str
