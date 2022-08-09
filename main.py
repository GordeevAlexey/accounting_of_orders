from utils import get_orders
from database.db import DBConnection
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from send_email import Email
from email.mime.text import MIMEText

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="static", autoescape=False, auto_reload=True)


@app.post("/add_task")
async def add_task(request: Request,
                   title: str = Form(),
                   daedline: str = Form(),
                   initiator: str = Form(),
                   employee: str = Form(),
                   department: str = Form(),
                   task_txt: str = Form()
                   ):

    DBConnection.add_order(title,
                           'Гордеев Алексей Николаевич',
                           initiator,
                           employee,
                           department,
                           task_txt,
                           datetime.now().strftime('%d.%m.%Y'),
                           daedline,
                           None,
                           'В работе',
                           None)

    mail_alert_txt = MIMEText(f"{employee}, Вам назначено поручение от {initiator}. <br> "\
                              f"<b>Срок исполнения до:</b> {daedline} <br> "\
                              f"<b>Поручение: </b> {task_txt}", "html")

    send_Email = Email()
    send_Email.send("abramovich@akcept.ru", mail_alert_txt)

    return templates.TemplateResponse('index.html', {'request': request})


@app.post("/update_task")
async def update(request: Request,
                      txt_close: str = Form(),
                      status: str = Form()):

    print(status)
    print(txt_close)

    # DBConnection.add_order(title,
    #                        'Гордеев Алексей Николаевич',
    #                        initiator,
    #                        employee,
    #                        department,
    #                        task_txt,
    #                        datetime.now().strftime('%d.%m.%Y'),
    #                        daedline,
    #                        None,
    #                        'В работе',
    #                        None)

    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/get_data")
async def get_task():
    return get_orders()


@app.get("/open_form")
async def add_task(request: Request):
    return templates.TemplateResponse('taskform.html', {'request': request})


@app.get("/")
async def start(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


if __name__ == "__main__":
    uvicorn.run("main:app",
                host="192.168.200.168",
                port=8004,
                reload=True)
