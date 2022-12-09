import json
from datetime import datetime
from database.pg_db import OrdersTable, SubOrdersTable, UsersTable, HistoryTable, Reports
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from send_email import Email
from database.utils import Action
from reminder_schedule import Reminder

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from reports import WeeklyReport


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

    js = json.dumps({
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
        })

    OrdersTable().add_order(js)
    return RedirectResponse("/", status_code=303)


@app.post("/add_suborder/{current_order_id}")
async def add_suborder(current_order_id: str,
                       employee_sub_order: list = Form(),
                       deadline: str = Form(),
                       content: str = Form()):

    js = json.dumps({
        "id_orders": current_order_id,
        "employee": ', '.join(employee_sub_order),
        "deadline": deadline,
        "content": content,
        "status_code": 'На исполнении'
        })

    suborder_id = SubOrdersTable().add_suborder(js)
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
    js = json.dumps({
        "id_orders": current_order_id,
        "id": current_suborder_id,
        "employee": ', '.join(employee_up),
        "deadline": deadline_up,
        "content": content_up
    })

    SubOrdersTable().update_suborder(js)
    users = UsersTable().select_users(employee_up)
    Email.send_info(current_suborder_id, users, Action.UPDATE)

    return RedirectResponse("/", status_code=303)


@app.post("/close_suborder/{current_order_id}/{current_suborder_id}/{response_type}")
async def close_suborder(request: Request,
                         current_order_id: str,
                         current_suborder_id: str,
                         response_type: str,
                         comment_suborder: str = Form()):

    js = json.dumps({
        "id_orders": current_order_id,
        "id": current_suborder_id,
        "comment": comment_suborder
    })

    SubOrdersTable().close_suborder(js)

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


@app.post("/reminder/start/", tags=["reminder"])
async def start_reminder():
    print("Планировщик создан")
    trigger = OrTrigger([
        CronTrigger(day_of_week=day, hour=6, minute=30)
            for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')])

    reminder_job = scheduler.add_job(
        Reminder().remind_to_employee,
        trigger=trigger,
        id="reminder",
        replace_existing=True,
    )
    return {"Scheduled": True, "JobID": reminder_job.id}


@app.post("/weekly_report/start", tags=["weekly_report"])
async def start_weekly_report():
    print("Планировщик еженедельного отчета создан")
    trigger = CronTrigger(day_of_week='fri', hour=14, minute=50)

    weekly_report_job = scheduler.add_job(
        WeeklyReport().send_report,
        trigger=trigger,
        id="weekly_report",
        replace_existing=True,
    )
    return {"Scheduled": True, "JobID": weekly_report_job.id}


@app.delete("/weekly_report/delete/", tags=["weekly_report"])
async def delete_weekly_report():
    print("Планировщик удален")
    scheduler.remove_job("weekly_report")
    return {"Scheduled": False, "JobID": "weekly_report"}


@app.delete("/reminder/delete/", tags=["reminder"])
async def delete_reminder():
    print("Планировщик удален")
    scheduler.remove_job("reminder")
    return {"Scheduled": False, "JobID": "reminder"}


if __name__ == "__main__":
    uvicorn.run("main:app",
                # host="192.168.200.92",
                host="192.168.200.168",
                # headers=[('server', 'top4ik')],
                port=8004,
                reload=True)
