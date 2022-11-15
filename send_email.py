from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from database.utils import User, Action
from database.utils import BodyMessage
from io import BytesIO


class Email:

    @staticmethod
    def _send(to: str, txt_body: str) -> None:
        msg = MIMEMultipart()
        msg['From'] = "exhorter@akcept.ru"
        msg['Subject'] = "Рассылка от системы поручений"
        msg['To'] = to
        msg.attach(MIMEText(txt_body, "html"))

        server = smtplib.SMTP("10.0.100.10", 25)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

    @staticmethod
    def send_info(id: str, users: list[User], action: Action):
        match action:
            case Action.ADD:
                message = BodyMessage.ADD.format(suborder_id=id)
            case Action.UPDATE:
                message = BodyMessage.UPDATE.format(suborder_id=id)
            case Action.DELETE:
                message = BodyMessage.DELETE.format(suborder_id=id)
            case Action.CLOSE:
                message = BodyMessage.CLOSE.format(suborder_id=id)
        [Email._send(email, message) for _, email in users]
    
    @staticmethod
    def send_weekly_report(txt_body: str, report_name: str, data: bytes) -> None:
        msg = MIMEMultipart()
        msg['From'] = "exhorter@akcept.ru"
        msg['Subject'] = "Еженедельный отчет по исполнению ВРД"
        # msg['To'] = 'sidorovich_ns@akcept.ru, gordeev_an@akcept.ru'
        msg['To'] = 'sidorovich_ns@akcept.ru'
        msg.attach(MIMEText(txt_body, "plain"))
        part = MIMEBase('application', 'vnd.ms-excel')
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={report_name}.xlsx")
        msg.attach(part)
        server = smtplib.SMTP("10.0.100.10", 25)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

