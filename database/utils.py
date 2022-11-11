from uuid import uuid4
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import NamedTuple
from enum import Enum


class BodyMessage(str, Enum):
    ADD ="""
        <pre>
        Добрый день.<br>
        Вам назначено новое поручение.<br>
        Перейдите по <a href="http://192.168.200.168:8004/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>"""
    UPDATE = """
        <pre>
        Добрый день.<br>
        Поручение обновлено.<br>
        Перейдите по <a href="http://192.168.200.168:8004/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """
    DELETE = """
        <pre>
        Добрый день.<br>
        Поручение удалено.<br>
        Перейдите по <a href="http://192.168.200.168:8004/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """
    CLOSE = """
        </pre>
        Добрый день.<br>
        Поручение закрыто.<br>

        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """
    WARNING_DELAY = """
        </pre>
        До окончания срока исполнения задачи осталось {days}!<br>
        Перейдите по <a href="http://192.168.200.168:8004/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>"""
    CRITICAL_DELAY = """
        </pre>
        Срок исполнения задачи истек!<br>
        Перейдите по <a href="http://192.168.200.168:8004/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>"""


class User(NamedTuple):
    name: str
    email: str


class Action(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    CLOSE = "close"
    DELAY = "delay"
    

@dataclass(frozen=True, slots=True)
class SuborderRow:
    id_orders: str
    id: str
    employee: str | None
    deadline: str | None
    content: str | None

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

