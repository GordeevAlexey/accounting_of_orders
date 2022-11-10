from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from enum import Enum
from database.utils import User, Action
from database.utils import BodyMessage


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

