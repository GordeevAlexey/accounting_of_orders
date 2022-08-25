import cx_Oracle
from abc import ABC, abstractmethod
import pandas as pd
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup as bs
import os
import json

load_dotenv()

IP=os.getenv('IP')
PORT=os.getenv('PORT')
SERVICE_NAME=os.getenv('SERVICE_NAME')
USER=os.getenv('USER')
PWD=os.getenv('PWD')


class IBSO(ABC):
    sql_file = None

    def __init__(self) -> None:
        dsn_tns = cx_Oracle.makedsn(IP, PORT, service_name=SERVICE_NAME)
        self.conn = cx_Oracle.connect(user=USER, password=PWD, dsn=dsn_tns)
        self.c = self.conn.cursor()
        self.c.execute("DECLARE x INTEGER; BEGIN x := ibs.lock_info.open; END;")

    @abstractmethod
    def _get_query(self, sql_file: str) -> str:
        if sql_file:
            with open(sql_file, 'r', encoding='utf-8') as query:
                return query.read()

    @abstractmethod
    def _get_data_from_db(self, query: str) -> pd.DataFrame:
        query = self._get_query()
        return pd.read_sql(query ,con=self.conn)


class Employees(IBSO):
    sql_file = 'database/sql/ibso_employees.sql'

    def __init__(self) -> None:
        super().__init__()

    def _get_query(self) -> str:
        return super()._get_query(self.sql_file)

    def _get_data_from_db(self) -> pd.DataFrame:
        query = self._get_query()
        return super()._get_data_from_db(query)

    def get_employees(self) -> json:
        df = self._get_data_from_db()
        groupped_divisions = df[['PRIVATE_PERSON', 'DIVISION']].groupby('DIVISION')\
                .agg({'PRIVATE_PERSON': lambda x: x.tolist()}).reset_index()
        employees = dict(zip(groupped_divisions.DIVISION, groupped_divisions.PRIVATE_PERSON))
        return json.dumps(employees)

    @staticmethod
    def get_phone_book() -> json:
        """
        Тянет данные с портала
        """
        phonebook = {}
        r = requests.get('http://portal/phonebook')
        soup = bs(r.text, "html.parser")
        main_table = soup.find_all('tr', class_='usTblContent')
        for table in main_table:
            table = tuple(map(lambda x: x.text.replace('\n', ''), table))
            phonebook.update(
                {
                table[3]: {
                    'position': table[5],
                    'mail': table[9],
                    'phone': table[11] or '-',
                }
            }
        )
        return json.dumps(phonebook)
