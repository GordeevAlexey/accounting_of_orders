from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from database.utils import User, Action, BodyMessage, order_type_incline


HOST = "http://10.0.2.47:8004"

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
    def send_info(id: str, order_info: tuple[str], users: list[User], action: Action):
        match action:
            case Action.ADD:
                message = BodyMessage.ADD
            case Action.UPDATE:
                message = BodyMessage.UPDATE
            case Action.DELETE:
                message = BodyMessage.DELETE
            case Action.CLOSE:
                message = BodyMessage.CLOSE
        order_type, issue_idx = order_info
        message = message.format(
            HOST=HOST,
            suborder_id=id,
            order=order_type_incline(order_type),
            issue_idx=issue_idx
        )
        [Email._send(email, message) for _, email in users]
    
    @staticmethod
    def send_weekly_report(txt_body: str, report_name: str, data: bytes) -> None:
        #https://stackoverflow.com/questions/1546367/python-how-to-send-mail-with-to-cc-and-bcc
        msg = MIMEMultipart()
        msg['From'] = "exhorter@akcept.ru"
        msg['Subject'] = "Еженедельный отчет об исполнении ВРД"
        to = 'azarova@akcept.ru,husnetinova_aa@akcept.ru'
        bcc = 'sidorovich_ns@akcept.ru,gordeev_an@akcept.ru'
        msg['To'] = to
        mailing_list = to.split(',') + bcc.split(',')

        msg.attach(MIMEText(txt_body, "plain"))
        part = MIMEBase('application', 'vnd.ms-excel')
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={report_name}.xlsx")
        msg.attach(part)

        server = smtplib.SMTP("10.0.100.10", 25)
        server.sendmail(msg['From'], mailing_list, msg.as_string())
        server.quit()

