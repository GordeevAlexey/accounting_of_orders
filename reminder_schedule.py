from database.pg_db import SubOrdersTable, OrdersTable
from send_email import Email
from database.utils import BodyMessage, order_type_incline
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
    def __init__(self) -> None:
        pass

    @staticmethod
    async def remind_to_employee() -> None:
        await Reminder._form_and_send(days=3)
        await Reminder._form_and_send()
    
    @staticmethod
    async def _form_and_send(days: int=0) -> None:
        message = BodyMessage.WARNING_DELAY if days else BodyMessage.CRITICAL_DELAY

        if delay_orders := await SubOrdersTable().get_delay_suborders(days):
            logger.info(f"Сработало напоминание по незакрытым поручениям: {delay_orders}")
            for order in delay_orders:
                order_type, issue_idx = OrdersTable().get_order(order['id_orders'])
                for _, email in order['employee']:
                    Email._send(
                        email,
                        message.format(
                            HOST=HOST,
                            suborder_id=order['id'],
                            order=order_type_incline(order_type),
                            issue_idx=issue_idx
                        )
                    )