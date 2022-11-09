from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from enum import Enum
from database.utils import User, Action
from database.pg_db import OrdersTable, UsersTable
import json


class Email:
    def __init__(self, id: str, users: list[User], action: Action):
        self.id = id
        self.users = users
        self.action = action

    def _send(self, to: str, txt_body: str) -> None:
        msg = MIMEMultipart()
        msg['From'] = "exhorter@akcept.ru"
        msg['Subject'] = "Рассылка от системы поручений"
        msg['To'] = to
        msg.attach(MIMEText(txt_body, "html"))

        server = smtplib.SMTP("10.0.100.10", 25)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

    def send(self):
        match self.action:
            case Action.ADD:
                message = BodyMessage.ADD.format(suborder_id=self.id)
            case Action.UPDATE:
                message = BodyMessage.UPDATE.format(suborder_id=self.id)
            case Action.DELETE:
                message = BodyMessage.DELETE.format(suborder_id=self.id)
            # case Action.CLOSE:
            #     message = BodyMessage.CLOSE.format(suborder_id=self.id)
        [self._send(email, message) for _, email in self.users]


class BodyMessage(str, Enum):
    ADD ="""
        <pre>
        Добрый день.
        Вам назначено новое поручение. Перейдите по ссылке для ознакомления.
        <a href="http://192.168.200.92/close_suborder/{suborder_id}">поручение</a>

        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>"""
    UPDATE = """
        <pre>
        Добрый день.
        Поручение обновлено. Перейдите по ссылке для ознакомления.
        <a href="http://192.168.200.92/close_suborder/{suborder_id}">поручение</a>

        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """
    DELETE = """
        <pre>
        Добрый день.
        Поручение удалено. Перейдите по ссылке для ознакомления.
        <a href="http://192.168.200.92/close_suborder/{suborder_id}">поручение</a>

        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """
    CLOSE = """
        Добрый день.
        Поручение закрыто. Перейдите по ссылке для ознакомления.
        <a href="http://192.168.200.92/close_suborder/{suborder_id}">поручение</a>

        *Данное письмо сформированно автоматически, не нужно на него отвечать.
        </pre>
        """


class Reminder:
    """
    Осуществляет проверку по просроченным поручениям для
    рассылки ответственным сотрудникам. Рассылка будет осуществляться за 3 дня 
    до окончания срока поручения, в день поручения и каждый день после нарушения
    сроков.
    """
    def __init__(self) -> None:
        self.users = json.loads(UsersTable().get_phone_book())

    def remind_to_employee(self) -> None:
        self._form_and_send(days=3)
        self._form_and_send()
    
    def _form_and_send(self, days: int=0) -> None:
        if days:
            message = MIMEText(
                "<b>До окончания срока исполнения задачи {title} осталось {days}!</b>",
                "html"
            )
        else:
            message = MIMEText(
                "<b>Срок исполнения задачи {title} истек!</b>",
                "html"
            )
        delay_orders = json.loads(SubordersTable.get_delay_orders(days))
        if delay_orders:
            for order in delay_orders:
                title = order.get('title')
                Email.send(
                    self.users.get(order['employee']),
                    message.format(title=title, days=days)
                )
                Email.send(
                    self.users.get(order['initiator']),
                    message.format(title=title, days=days)
                )


