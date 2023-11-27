
FROM python:3.10.4
WORKDIR /usr/src/accounting_of_orders
COPY . .
ENV TZ="Asia/Novosibirsk"
RUN unzip /usr/src/accounting_of_orders/opt/oracle/instantclient-basic-linux.x64-21.6.0.0.0dbru.zip
RUN sh -c "echo /usr/src/accounting_of_orders/instantclient_21_6 > /etc/ld.so.conf.d/oracle-instantclient.conf"
RUN dpkg -i /usr/src/accounting_of_orders/opt/oracle/libaio1_0.3.112-9_amd64.deb
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade -r requirements.txt
CMD ["python3", "main.py"]




