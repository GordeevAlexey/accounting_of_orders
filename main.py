import json
from datetime import datetime
#from database.db import OrdersTable, SubOrdersTable, ReportDatabaseWriter
from database.pg_db import OrdersTable, SubOrdersTable, UsersTable, HistoryTable
from database.ibso import Employees
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from send_email import Email
from email.mime.text import MIMEText
#from reports import Report
from fastapi.responses import StreamingResponse
from database.utils import Action


app = FastAPI()
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
                    deadline: str = Form(),
                    comment: str = Form(),
                    reference: str = Form()):

    print(datetime.strptime(approving_date, '%Y-%m-%d').strftime('%d.%m.%Y'))

    js = json.dumps({
        "issue_type": issue_type,
        "issue_idx": issue_idx,
        "approving_date": datetime.strptime(approving_date, '%Y-%m-%d').strftime("%d.%m.%Y"),
        "title": title,
        "initiator": ', '.join(initiator),
        "approving_employee": ', '.join(approving_employee),
        "deadline": datetime.strptime(deadline, '%Y-%m-%d').strftime("%d.%m.%Y"),
        "comment": comment,
        "reference": reference,
        "status_code": 'На исполнении'
        })

    #OrdersTable.add_order(js)
    OrdersTable().add_order(js)
    return RedirectResponse("/", status_code=303)


@app.post("/add_suborder/{current_order_id}")
async def add_suborder(current_order_id: str,
                       employee: list = Form(),
                       deadline: str = Form(),
                       content: str = Form()):

    js = json.dumps({
        "id_orders": current_order_id,
        "employee": str(', '.join(employee)),
        "deadline": datetime.strptime(deadline, '%Y-%m-%d').strftime("%d.%m.%Y"),
        "content": content,
        "status_code": 'На исполнении'
        })

    suborder_id = SubOrdersTable().add_suborder(js)
    users = UsersTable().select_users(employee)
    Email(suborder_id, users, Action.ADD).send()

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
        "employee": str(', '.join(employee_up)),
        "deadline": datetime.strptime(deadline_up, '%Y-%m-%d').strftime("%d.%m.%Y"),
        "content": content_up
    })

    SubOrdersTable().update_suborder(js)
    users = UsersTable().select_users(employee_up)
    Email(current_suborder_id, users, Action.UPDATE).send()

    return RedirectResponse("/", status_code=303)


@app.post("/close_suborder/{current_order_id}/{current_suborder_id}")
async def close_suborder(current_order_id: str,
                         current_suborder_id: str,
                         ):
    #comment_suborder: str = Form()
    js = json.dumps({
        "id_orders": current_order_id,
        "id": current_suborder_id,
        "status_code": "Завершено",
     #   "comment": comment_suborder
    })

    SubOrdersTable().update_suborder(js)

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
    return ReportDatabaseWriter.get_info(suborder_id)


@app.get("/")
async def start(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/get_users")
async def get_users():
    return UsersTable().get_users()

# @app.get("/get_order_report", response_description='xlsx')
# async def get_task_order_report():
#     #Скачивает отчет
#     r = Report()
#     r.get_report()
#     headers = {
#         'Content-Disposition': 'attachment; filename="report.xlsx"'
#     }
#     return StreamingResponse(r.output, headers=headers)

if __name__ == "__main__":
    uvicorn.run("main:app",
                host="192.168.200.92",
                # host="192.168.200.168",
                # headers=[('server', 'top4ik')],
                port=8004,
                reload=True)
