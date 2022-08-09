from email.mime.multipart import MIMEMultipart
import smtplib


class Email():

    def send(self, to, txt_body):

        msg = MIMEMultipart()
        msg['From'] = "mail@akcept.ru"
        msg['To'] = to
        msg.attach(txt_body)

        server = smtplib.SMTP("10.0.100.10", 25)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
