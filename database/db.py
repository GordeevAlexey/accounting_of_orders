import sqlite3
from functools import wraps
from pypika import Query, Table
from uuid import uuid4
from datetime import date, datetime
import json
import pandas as pd
from datetime import datetime, timedelta

#sqlite3.IntegrityError: UNIQUE constraint failed: USERS.email


class DBConnector:

    def __init__(self):
       self.conn = None

    def create_connection(self):
        return sqlite3.connect('./database.db', isolation_level=None)

    def __enter__(self):
        self.conn = self.create_connection()
        return self.conn

    def __exit__(self):
        self.conn.close()


class DBConnection:
    connection = None

    @classmethod
    def _get_connection(cls, new=False):
        """Creates return new Singleton database connection"""
        if new or not cls.connection:
            cls.connection = DBConnector().create_connection()
        return cls.connection

    @staticmethod
    def cursor_add(method):
        @wraps(method)
        def wrapper(cls, *args):
            connection = cls._get_connection()
            try:
                cursor = connection.cursor()
            except sqlite3.Error:
                connection = cls._get_connection(new=True)  # Create new connection
                cursor = connection.cursor()
            return method(cls, cursor, *args)
        return wrapper

    @classmethod
    @cursor_add
    def _create_tables(cls, cursor, schema_path: str):
        with open(schema_path, 'r', encoding='utf-8') as query:
            tables_creation_request = query.read()
        cursor.executescript(tables_creation_request)
        cursor.close()

    @classmethod
    @cursor_add
    def execute_query(cls, cursor, query):
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

class OrdersTable(DBConnection):
    """
    Работа с таблицей Поручений
    """
    @classmethod
    @DBConnection().cursor_add
    def _get_orders_header(cls, cursor):
        #Возвращает все имена столбцов таблицы ORDERS
        try:
            cursor.execute("PRAGMA table_info(ORDERS)") 
            headers = [row[1] for row in cursor.fetchall()]
            return headers
        except:
            return None
        finally:
            cursor.close()

    @classmethod
    @DBConnection().cursor_add
    def get_delay_orders(cls, cursor, days: int = 0):
        """
        """
        delay_date = datetime.today() + timedelta(days=days)
        table = Table('ORDERS')
        cols = (
            'id',
            'title',
            'initiator',
            'employee',
            'deadline'
        )
        q = Query.from_(table).select(*cols)\
            .where(
                (table.deleted == False) & (table.status != 'Исполнено')
                & (table.deadline == delay_date.strftime('%d.%m.%Y'))
            )
        cursor.execute(str(q))
        delay_orders = cursor.fetchall()
        cursor.close()
        if delay_orders:
            delay_orders = json.dumps([{k: v for k,v in zip(cols, row)} for row in delay_orders])
        else:
            delay_orders = None
        return delay_orders

    @classmethod
    @DBConnection().cursor_add
    def get_orders_table(cls, cursor, table_name: str):
        #Полная выгрузка
        headers = OrdersTable()._get_orders_header()
        table = Table(table_name)
        q = Query.from_(table).select(table.star)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)
    
    #TODO: Доработать с новыми изменениями
    @classmethod
    @DBConnection().cursor_add
    def get_orders_report_data(cls, cursor):
        #Выгрузка по форме отчета
        headers = (
            'issue_type',
            'issue_idx',
            'approving_date',
            'title',
            'initiator',
            'approving_employee',
            'employee',
            'deadline',
            'status_code',
            'close_date',
            'comment',
        )
        table = Table('ORDERS')
        q = Query.from_(table).select(
            table.issue_type,
            table.issue_idx,
            table.approving_date,
            table.title,
            table.initiator,
            table.approving_employee,
            table.employee,
            table.deadline,
            table.status_code,
            table.close_date,
            table.comment
        )
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)

    @classmethod
    @DBConnection().cursor_add
    def add_order(cls, cursor, row: json, table_name: str):
        table = Table(table_name)
        row = json.loads(row)
        _columns = row.keys()
        q = Query.into(table).columns(
            'id', 'deleted',
            'create_date', 'update_date',
            *_columns
        )\
            .insert(
                uuid4(), False, datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                None, *row.values()
        )
        cursor.execute(str(q))
        cursor.close()
        print(f"Поручение добавлено")

    @classmethod
    @DBConnection().cursor_add
    def update_order(cls, cursor, data: json):
        #Обязательно должен быть передан id записи
        data = json.loads(data)
        table = Table('ORDERS')
        q = Query.update(table).where(table.id == data['id'])\
            .set('update_date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        for key in data:
            q = q.set(key, data[key])
        cursor.execute(str(q))
        cursor.close()
        print(f'Успешно обновленны данные id:{data["id"]}')


class ReportDatabaseWriter(OrdersTable):
    """
    Запись из Excel в базу
    """
    cols = (
            "create_date",
            "issue_idx",
            "approving_date",
            "title",
            "initiator",
            "approving_employee",
            "employee",
            "deadline",
            "status_code",
            "close_date",
            "comment"
    )
    def __init__(self, excel_report: str|bytes) -> None:
        self.excel_report = excel_report

    def _handle_excel_report(self) -> json:
        #TODO: Доработать формат Excel в столбцах с датами
        df = pd.read_excel(self.excel_report, header=None, skiprows=4)
        df.columns = self.cols
        df = df.to_dict('records')
        return json.dumps(df)
    
    def excel_to_db(self) -> None:
        rows = self._handle_excel_report()
        for row in rows:
            super().add_order(row)
        

# OrdersTable().get_delay_orders()
data = {
    'issue_type': 'Приказ',
    'issue_idx': '586',
    'approving_date': '19.07.2022',
    'title': "Об актуализации плана  реализации проекта  по использованию биометрической идентификации при обслуживании физических лиц",
    'initiator': 'Сергунина Е.В.',
    'approving_employee':'Терехина Е.С.',
    'deadline': '28.08.2022',
    'status_code': 'В работе',
    'close_date': '',
    'comment': '',
    'reference': 'C:\Users\sidorovich_ns\Desktop\Projects\accounting_of_orders\income\Приказ_продажа монет кассовым работником.doc',
}
OrdersTable.add_order(data)





