from database.pg_db import OrdersTable, SubOrdersTable, UsersTable, Reports

import uvicorn
from fastapi import FastAPI, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, FileResponse
from starlette.templating import Jinja2Templates

from send_email import Email
from database.utils import Action, employees_to_string

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from reports import *
import logging
from logger.logger import *
from database.data import *
from schedulers import *


logger = logging.getLogger(__name__)

app = FastAPI()

scheduler = AsyncIOScheduler()
scheduler.start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="static", autoescape=False, auto_reload=True)


@app.post("/update_order")
async def update_order(order=Depends(Order)):
    o = order.dict()
    employees_to_string(o)
    OrdersTable().update_order(o)
    return RedirectResponse("/", status_code=303)


@app.post("/delete_order")
async def delete_order(id: str):
    OrdersTable().delete_order_row(id)
    return RedirectResponse("/", status_code=303)


@app.post("/add_order")
async def add_order(issue_idx: str = Form(),
                    issue_type: str = Form(),
                    approving_date: str = Form(),
                    title: str = Form(),
                    initiator: list = Form(),
                    approving_employee: list = Form(),
                    employee_order: list = Form(),
                    deadline: str = Form(),
                    comment: str = Form(),
                    reference: str = Form()):

    data = {
        "issue_type": issue_type,
        "issue_idx": issue_idx,
        "approving_date": approving_date,
        "title": title,
        "initiator": ', '.join(initiator),
        "approving_employee": ', '.join(approving_employee),
        "deadline": deadline,
        "employee": ', '.join(employee_order),
        "comment": comment,
        "reference": reference,
        "status_code": 'На исполнении'
        }

    OrdersTable().add_order(data)
# @app.post("/add_order")
# async def add_order(order = Depends(NewOrder)):
#     o = order.dict()
#     print(o)
#     employees_to_string(o)
#     OrdersTable().add_order(o)
    return RedirectResponse("/", status_code=303)


@app.post("/add_suborder/{current_order_id}")
async def add_suborder(current_order_id: str,
                       employee_sub_order: list = Form(),
                       deadline: str = Form(),
                       content: str = Form()):

    data = {
        "id_orders": current_order_id,
        "employee": ', '.join(employee_sub_order),
        "deadline": deadline,
        "content": content,
        "status_code": 'На исполнении'
        }

    suborder_id = SubOrdersTable().add_suborder(data)
    users = UsersTable().select_users(employee_sub_order)
    Email.send_info(suborder_id, users, Action.ADD)

    return RedirectResponse("/", status_code=303)


@app.post("/update_suborder/{current_order_id}/{current_suborder_id}")
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
    users = UsersTable().select_users(employee_up)
    Email.send_info(current_suborder_id, users, Action.UPDATE)

    return RedirectResponse("/", status_code=303)


@app.post("/close_suborder/{current_order_id}/{current_suborder_id}/{response_type}")
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


@app.post("/delete_suborder/{current_order_id}/{current_suborder_id}")
async def delete_suborder(current_order_id: str,
                          current_suborder_id: str):
    SubOrdersTable().delete_suborder_row(current_order_id, current_suborder_id)
    return RedirectResponse("/", status_code=303)


@app.get("/get_order")
async def get_order():
    return OrdersTable().get_orders_table_pg_bar()


@app.get("/get_suborder/{order_id}")
async def get_suborder(order_id: str):
    return SubOrdersTable().get_suborders_table(order_id)


@app.get("/close_suborder/{suborder_id}")
async def close_suborder(suborder_id: str, request: Request):
    return templates.TemplateResponse('close_suborder.html',
                                      {'request': request, 'suborder_id': suborder_id})


@app.get("/get_info_for_close_suborder/{suborder_id}")
async def get_info_for_close_suborder(suborder_id: str):
    return Reports().get_info_suborder(suborder_id)


@app.get("/")
async def start(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/get_users")
async def get_users():
    return UsersTable().get_users()

@app.on_event("startup")
async def startup():
    """
    Запуск планировщиков
    """
    remind_to_employ(scheduler)
    send_weekly_report(scheduler)
    table_update(scheduler)

@app.get("/logs")
async def show_get_logs():
    logger.info('Выгрузка логов.')
    return FileResponse(path='logs.log', filename='logs.log', media_type='text/mp4')


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
            host="0.0.0.0",
            port=8004,
            reload=True,
            log_level="error"
    )
        
