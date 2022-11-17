from uuid import uuid4
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import NamedTuple, Any, Optional
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


def date_formatter(json: dict[str, Any]) -> None:
    if not json:
        return {}
    for key, value in json.items():
        if key in ('create_date', 'update_date', 'close_date', 'change_date'):
            json[key] = None if value is None else value.strftime("%d.%m.%Y %H:%M:%S")
        elif key in ('deadline', 'approving_date'):
            json[key] = None if value is None else value.strftime("%d.%m.%Y")
    return json


