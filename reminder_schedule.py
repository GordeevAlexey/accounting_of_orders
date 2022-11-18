
from database.pg_db import SubOrdersTable
from send_email import Email
from database.utils import BodyMessage


class Reminder:
    """
    Осуществляет проверку по просроченным поручениям для
    рассылки ответственным сотрудникам. Рассылка будет осуществляться за 3 дня 
    до окончания срока поручения, в день поручения и каждый день после нарушения
    сроков.
    """

    @staticmethod
    def remind_to_employee() -> None:
        Reminder._form_and_send(days=3)
        Reminder._form_and_send()
    
    @staticmethod
    def _form_and_send(days: int=0) -> None:
        if days:
            message = BodyMessage.WARNING_DELAY
        else:
            message = BodyMessage.CRITICAL_DELAY

        delay_orders = SubOrdersTable().get_delay_suborders(days)
        print(delay_orders)
        if delay_orders:
            for order in delay_orders:
                for _, email in order['employee']:
                    to = email
                    Email._send(to, message.format(suborder_id=order['id']))
