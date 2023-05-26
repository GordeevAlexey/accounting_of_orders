from typing import NamedTuple, Any
from enum import Enum


HOST = "http://10.0.2.47:8004"

class BodyMessage(str, Enum):
    ADD ="""
        <pre>
        Добрый день.<br>
        Вам назначено новое поручение.<br>
        Перейдите по <a href="{HOST}/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>"""
    UPDATE = """
        <pre>
        Добрый день.<br>
        Поручение обновлено.<br>
        Перейдите по <a href="{HOST}/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>
        """
    DELETE = """
        <pre>
        Добрый день.<br>
        Поручение удалено.<br>
        Перейдите по <a href="{HOST}/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>
        """
    CLOSE = """
        </pre>
        Добрый день.<br>
        Поручение закрыто.<br>

        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>
        """
    WARNING_DELAY = """
        </pre>
        До окончания срока исполнения задачи осталось 3 дня!<br>
        Перейдите по <a href="{HOST}/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>"""
    CRITICAL_DELAY = """
        </pre>
        Срок исполнения задачи истек!<br>
        Перейдите по <a href="{HOST}/close_suborder/{suborder_id}">ссылке</a> для ознакомления.<br><br>
        *Данное письмо сформировано автоматически, не нужно на него отвечать.
        </pre>"""


class User(NamedTuple):
    user_name: str
    email: str


class Action(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    CLOSE = "close"
    DELAY = "delay"


def employees_to_string(order: dict):
    for key in ("initiator", "approving_employee", "employee"):
        order[key] = ', '.join(order[key])


def date_formatter(json: dict[str, Any]) -> dict:
    if not json:
        return {}
    for key, value in json.items():
        if key in ('create_date', 'update_date', 'close_date', 'change_date'):
            json[key] = None if value is None else value.strftime("%d.%m.%Y %H:%M:%S")
        elif key in ('deadline', 'approving_date'):
            json[key] = None if value is None else value.strftime("%d.%m.%Y")
    return json


def query_from_file(sql_file: str) -> str:
    """
    Чтение запроса из файла
    """
    with open(sql_file, 'r', encoding='utf-8') as file:
        return file.read()


