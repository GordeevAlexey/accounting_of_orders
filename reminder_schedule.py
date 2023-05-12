from database.pg_db import SubOrdersTable
from send_email import Email
from database.utils import BodyMessage
import logging
from logger.logger import *


logger = logging.getLogger(__name__)


HOST = "http://10.0.2.47:8004"

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
        message = BodyMessage.WARNING_DELAY if days else BodyMessage.CRITICAL_DELAY

        if delay_orders := SubOrdersTable().get_delay_suborders(days):
            logger.info(f"Сработало напоминание по незакрытым поручениям: {delay_orders}")
            [
                Email._send(email, message.format(HOST=HOST,suborder_id=order['id']))
                for order in delay_orders for _, email in order['employee'] 
            ]