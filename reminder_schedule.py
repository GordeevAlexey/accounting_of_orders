from database.pg_db import SubOrdersTable, OrdersTable
from send_email import Email
from database.utils import BodyMessage, order_type_inline
import logging
from logger.logger import *
from common import HOST


logger = logging.getLogger(__name__)


class Reminder:
    """
    Осуществляет проверку по просроченным поручениям для
    рассылки ответственным сотрудникам. Рассылка будет осуществляться за 3 дня 
    до окончания срока поручения, в день поручения и каждый день после нарушения
    сроков.
    """

    @staticmethod
    async def remind_to_employee() -> None:
        await Reminder._form_and_send(3)
        await Reminder._form_and_send(1)
        await Reminder._form_and_send(0)
    
    @staticmethod
    async def _form_and_send(days: int) -> None:
        match days:
            case 0:
                message = BodyMessage.TODAY
            case 1:
                message = BodyMessage.CRITICAL_DELAY
            case 3:
                message = BodyMessage.WARNING_DELAY

        if delay_orders := await SubOrdersTable().get_delay_suborders(days):
            for order in delay_orders:
                order_info = OrdersTable().get_order(order['id_orders'])
                _deadline = '.'.join(order['deadline'].split('-')[::-1])
                for _, email in order['employee']:
                    Email._send(
                        email,
                        message.format(
                            HOST=HOST,
                            suborder_id=order['id'],
                            order=order_type_inline(order_info['issue_type']),
                            issue_idx=order_info['issue_idx']
                        ),
                        f"Рассылка от системы поручений. {order_info['issue_type']} №{order_info['issue_idx']}. Дедлайн: {_deadline}"
                    )
                    logger.info(
                        f"Напоминание по незакрытому поручению: "\
                        f"id: {order['id']}, "\
                        f"{email}, "\
                        f"№{order_info['issue_idx']}, "\
                        f"deadline: {_deadline}"
                    )