from database.db import OrdersTable
from database.ibso import Employees
from email.mime.text import MIMEText
import json
from send_email import Email 


class Reminder:
    """
    Осуществляет проверку по просроченным поручениям для
    рассылки ответственным сотрудникам. Рассылка будет осуществляться за 3 дня 
    до окончания срока поручения, в день поручения и каждый день после нарушения
    сроков.
    """
    def __init__(self) -> None:
        self.phone_book = json.loads(Employees().get_phone_book())

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
        delay_orders = json.loads(OrdersTable.get_delay_orders(days))
        if delay_orders:
            for order in delay_orders:
                title = order.get('title')
                Email.send(
                    self.phone_book.get(order['employee']),
                    message.format(title=title, days=days)
                )
                Email.send(
                    self.phone_book.get(order['initiator']),
                    message.format(title=title, days=days)
                )

