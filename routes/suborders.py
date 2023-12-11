from fastapi import APIRouter, Depends, HTTPException, Request
from database.pg_db import Reports
import logging
from logger.logger import *


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/suborder", tags=['suborder'])

@router.patch("/update/{current_order_id}/{current_suborder_id}")
async def update_suborder(current_order_id: str,
                          current_suborder_id: str,
                          employee_up: list = Form(),
                          deadline_up: str = Form(),
                          content_up: str = Form()
                          ):
    data = {
        "id_orders": current_order_id,
        "id": current_suborder_id,
        "employee": ', '.join(employee_up),
        "deadline": deadline_up,
        "content": content_up
    }

    SubOrdersTable().update_suborder(data)
    users = await UsersTable().select_users(employee_up)
    info_order = OrdersTable().get_order(current_order_id)
    info_order['deadline'] = deadline_up
    Email.send_info(current_suborder_id, info_order, users, Action.UPDATE)
    return RedirectResponse("/", status_code=303)


@router.post("/close_suborder/{current_order_id}/{current_suborder_id}/{response_type}")
async def close_suborder(request: Request,
                         current_order_id: str,
                         current_suborder_id: str,
                         response_type: str,
                         comment_suborder: str = Form()):

    data = {
        "id_orders": current_order_id,
        "id": current_suborder_id,
        "comment": comment_suborder
    }

    SubOrdersTable().close_suborder(data)

    if response_type == 'closing_by_the_performer':
        return templates.TemplateResponse('close_suborder.html', {'request': request,
                                                                  'suborder_id': current_suborder_id})
    elif response_type == 'closing_by_the_administrator':
        return RedirectResponse("/", status_code=303)


@router.get("/get_info_for_close_suborder/{suborder_id}")
async def get_info_for_close_suborder(suborder_id: str):
    return Reports().get_info_suborder(suborder_id)