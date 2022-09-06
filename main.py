from database.db import DBConnection
import uvicorn
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from send_email import Email
from email.mime.text import MIMEText
from reports import OrderReport
from fastapi.responses import StreamingResponse
from schedule import every, run_pending, repeat
from multiprocessing import Process
from database.db import Dumper
from starlette.responses import FileResponse


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="static", autoescape=False, auto_reload=True)


@app.get("/check_result")
async def check_result():
    global RESULT
    print(RESULT)



@app.post("/add_task")
async def add_task(request: Request,
                   issue_type: str = Form(),
                   initiator: str = Form(),
                   title: str = Form(),
                   issue_date: str = Form(),
                   employee: str = Form(),
                   status_code: str = Form(),
                   deadline: str = Form(),
                   close_date: str = Form(),
                   comment: str = Form(),
                   reference: str = Form(),
                   ):

    DBConnection.add_order(
        issue_type,
        initiator,
        title,
        issue_date,
        employee,
        status_code,
        deadline,
        close_date,
        comment,
        reference,
    )

    mail_alert_txt = MIMEText(f"{employee}, Вам назначено поручение от {initiator}. <br> "\
                              f"<b>Срок исполнения до:</b> {deadline} <br> "\
                              f"<b>Поручение: </b> {title}", "html")

    send_Email = Email()
    send_Email.send("sidorovich@akcept.ru", mail_alert_txt)

    return templates.TemplateResponse('index.html', {'request': request})


@app.post("/update_task")
async def update(request: Request,
                      txt_close: str = Form(),
                      status: str = Form()):

    print(status)
    print(txt_close)

    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/get_data", response_description='xlsx')
async def get_task():
    #Скачивает отчет
    r = OrderReport()
    r.get_report()
    headers = {
        'Content-Disposition': 'attachment; filename="report.xlsx"'
    }
    return StreamingResponse(r.output, headers=headers)


@app.get("/open_form")
async def add_task(request: Request):
    return templates.TemplateResponse('taskform.html', {'request': request})


@app.get("/")
async def start(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/dump")
async def get_dump_db():
    #Возвращает sql дамп базы
    dump_path = Dumper().create_dump()
    return FileResponse(
        dump_path,
        media_type='application/octet-stream',
        filename=dump_path
    )


if __name__ == "__main__":
    # jobs = []
    # p1 = Process(target=good_luck)
    # jobs.append(p1)
    # p1.start()
    uvicorn.run("main:app",
                host="192.168.200.92",
                port=8004,
                reload=True)
