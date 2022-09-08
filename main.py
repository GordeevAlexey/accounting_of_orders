import json

from database.db import DBConnection, OrdersTable, SubOrdersTable
from database.ibso import Employees
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from send_email import Email
from email.mime.text import MIMEText
#from reports import Report
from fastapi.responses import StreamingResponse


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
async def add_order(request: Request,
                   issue_type: str = Form(),
                   issue_idx: str = Form(),
                   approving_date: str = Form(),
                   title: str = Form(),
                   initiator: list = Form(),
                   approving_employee: list = Form(),
                   deadline: str = Form(),
                   comment: str = Form(),
                   reference: str = Form()):

    js = json.dumps({
        "issue_type": issue_type,
        "issue_idx": issue_idx,
        "approving_date": approving_date,
        "title": title,
        "initiator": str(', '.join(initiator)),
        "approving_employee": str(', '.join(approving_employee)),
        "deadline": deadline,
        "comment": comment,
        "reference": reference,
        "status_code": 'На исполнении'
        })

    OrdersTable.add_order(js)

    return RedirectResponse("/", status_code=303)


@app.post("/add_suborder")
async def add_suborder(request: Request,
                   current_order_id: str = Form(),
                   employee: list = Form(),
                   deadline: str = Form(),
                   content: str = Form()):

    js = json.dumps({
        "id_orders": current_order_id,
        "employee": str(', '.join(employee)),
        "deadline": deadline,
        "content": content,
        "status_code": 'На исполнении'
        })

    SubOrdersTable.add_suborder(js)

    return RedirectResponse("/", status_code=303)


@app.post("/update_task")
async def update(request: Request,
                      txt_close: str = Form(),
                      status: str = Form()):

    print(status)
    print(txt_close)

    return RedirectResponse("/", status_code=303)


# @app.get("/get_order_report", response_description='xlsx')
# async def get_task_order_report():
#     #Скачивает отчет
#     r = Report()
#     r.get_report()
#     headers = {
#         'Content-Disposition': 'attachment; filename="report.xlsx"'
#     }
#     return StreamingResponse(r.output, headers=headers)


@app.get("/get_order")
async def get_order():
    return OrdersTable().get_orders_table()


@app.get("/get_suborder/{order_id}")
async def get_suborder(order_id: str):
    return SubOrdersTable().get_suborders_table(order_id)


@app.get("/open_form")
async def add_task(request: Request):
    return templates.TemplateResponse('taskform.html', {'request': request})


@app.get("/")
async def start(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/get_users")
async def get_users():
    return json.loads(Employees().get_phone_book_for_selected())


if __name__ == "__main__":
    uvicorn.run("main:app",
                host="192.168.200.168",
                # headers=[('server', 'top4ik')],
                port=8004,
                reload=True)
