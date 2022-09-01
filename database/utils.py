from uuid import uuid4
from dataclasses import dataclass, asdict
from datetime import datetime
from reminder import Reminder
from schedule import every, run_pending, repeat


@dataclass(frozen=True, slots=True)
class OrderRow:
    id: uuid4
    deleted: bool
    create_date: datetime
    update_date: datetime
    issue_type: str
    issue_idx: int
    approving_date: datetime
    title: str
    initiator: str
    approving_employee: str
    employee: str
    deadline: datetime
    status_code: str
    close_date: datetime
    comment: str
    reference: str


@dataclass(frozen=True, slots=True)
class Order:
    order_rows: list[OrderRow]


# @repeat(every().day.at("06:00"))
@repeat(every(15).seconds)
def check_delay_orders():
    global three_days_delay
    global execution_period_end
    three_days_delay = Reminder().three_days_delay
    execution_period_end= Reminder().three_days_delay 
