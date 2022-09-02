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
    def _create_tables(cls, cursor, schema_path: str = None):
        if schema_path:
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

    table = Table("ORDERS")

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
    def get_delay_orders(cls, cursor, days: int = 0) -> json:
        """
        Возвращает выборку по просроченным поручениям.
        """
        delay_date = datetime.today() + timedelta(days=days)
        cols = (
            'id',
            'create_date',
            'update_date',
            'issue_type',
            'issue_idx',
            'title',
            'initiator',
            'employee',
            'deadline',
            'performance_note',
            'comment',
            'reference',
        )
        q = Query.from_(cls.table).select(*cols)\
            .where(
                (cls.table.deleted == False) & (cls.table.status_code != 'Исполнено')
                & (cls.table.deadline == delay_date.strftime('%d.%m.%Y'))
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
    def get_orders_table(cls, cursor) -> json:
        #Полная выгрузка
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == False)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)
    
    @classmethod
    @DBConnection().cursor_add
    def _get_deleted_orders_rows(cls, cursor) -> json:
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == True)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)

    #TODO: Доработать с новыми изменениями
    @classmethod
    @DBConnection().cursor_add
    def get_orders_report_data(cls, cursor) -> json:
        #Выгрузка по форме отчета
        headers = (
            'id',
            'issue_type',
            'issue_idx',
            'approving_date',
            'title',
            'initiator',
            'approving_employee',
            'deadline',
            'status_code',
            'close_date',
            'comment',
            'performance_note',
        )
        q = Query.from_(cls.table).select(*headers).where(cls.table.deleted == False)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)

    @classmethod
    @DBConnection().cursor_add
    def add_order(cls, cursor, row: json) -> None:
        table = Table('ORDERS')
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
    def delete_order_row(cls, cursor, id: bytes) -> None:
        id = id.decode('utf-8')
        q = Query.update(cls.table).where(cls.table.id == id)\
            .set('deleted', True)
        cursor.execute(str(q))
        cursor.close()
        print(f'Строка с id {id} "удалена" из orders.')

    @classmethod
    @DBConnection().cursor_add
    def update_order(cls, cursor, data: json) -> None:
        #Обязательно должен быть передан id записи
        data = json.loads(data)
        q = Query.update(cls.table).where(cls.table.id == data['id'])\
            .set('update_date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        for key in data:
            q = q.set(key, data[key])
        cursor.execute(str(q))
        cursor.close()
        print(f'Успешно обновленны данные id:{data["id"]}')


class SubOrdersTable(DBConnection):
    """
    Работа с подзадачами в поручении/приказе
    """

    table = Table('SUBORDERS')

    @classmethod
    @DBConnection().cursor_add
    def _get_suborders_header(cls, cursor):
        #Возвращает все имена столбцов таблицы SUBORDERS
        try:
            cursor.execute("PRAGMA table_info(SUBORDERS)") 
            headers = [row[1] for row in cursor.fetchall()]
            return headers
        except:
            return None
        finally:
            cursor.close()

    @classmethod
    @DBConnection().cursor_add
    def get_delay_suborders(cls, cursor, id_orders: bytes, days: int = 0) -> json:
        """
        Возвращает выборку по просроченным поручениям.
        """
        id_orders = id_orders.decode('utf-8')
        delay_date = datetime.today() + timedelta(days=days)
        cols = (
            'id',
            'id_orders',
            'title',
            'employee',
            'content',
            'deadline'
        )
        q = Query.from_(cls.table).select(*cols)\
            .where(
                (cls.table.deleted == False) & (cls.table.status_code != 'Исполнено')
                & (cls.table.deadline == delay_date.strftime('%d.%m.%Y'))
                &(cls.table.id_orders == id_orders)
            )
        cursor.execute(str(q))
        sub_orders = cursor.fetchall()
        cursor.close()
        if sub_orders:
            sub_orders = json.dumps([{k: v for k,v in zip(cols, row)} for row in sub_orders])
        else:
            sub_orders = None
        return sub_orders

    @classmethod
    @DBConnection().cursor_add
    def get_suborders_table(cls, cursor, id_orders: bytes) -> json:
        #Выгрзука подзадач по отдельному приказу или поручению
        id_orders = id_orders.decode('utf-8')
        headers = SubOrdersTable()._get_suborders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == False)
        cursor.execute(str(q))
        suborders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in suborders]
        cursor.close()
        return json.dumps(result)
    
    #TODO: Доработать с новыми изменениями
    @classmethod
    @DBConnection().cursor_add
    def get_suborders_report_data(cls, cursor, id_orders: bytes) -> json:
        #Выгрузка по форме отчета
        id_orders = id_orders.decode('utf-8')
        headers = (
            'employee',
            'deadline',
            'content',
            'performance_note',
            'status_code',
            'close_date',
            'comment',
        )
        q = Query.from_(cls.table).select(*headers)\
            .where(
                (cls.table.id_orders == id_orders) & (cls.table.deleted == False)
            )
        cursor.execute(str(q))
        suborders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in suborders]
        cursor.close()
        return json.dumps(result)

    @classmethod
    @DBConnection().cursor_add
    def add_suborder(cls, cursor, row: json) -> None:
        row = json.loads(row)
        _columns = row.keys()
        q = Query.into(cls.table).columns(
            'id', 'deleted',
            'create_date', 'update_date',
            *_columns
        )\
            .insert(
                uuid4(), False,
                datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                None, *row.values()
            )
        cursor.execute(str(q))
        cursor.close()
        print(f"Поручение добавлено")

    @classmethod
    @DBConnection().cursor_add
    def update_suborder(cls, cursor, data: json) -> None:
        #Обязательно должен быть передан id записи
        data = json.loads(data)
        q = Query.update(cls.table).where(
            (cls.table.id == data['id'])
            & (cls.table.id_orders == data['id_orders'])
            )\
            .set('update_date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        for key in data:
            q = q.set(key, data[key])
        cursor.execute(str(q))
        cursor.close()
        print(f'Успешно обновленны данные id:{data["id"]}')

    @classmethod
    @DBConnection().cursor_add
    def delete_suborder_row(cls, cursor, id: bytes) -> None:
        id = id.decode('utf-8')
        q = Query.update(cls.table).where(cls.table.id == id)\
            .set('deleted', True)
        cursor.execute(str(q))
        cursor.close()
        print(f'Строка с id {id} "удалена" из suborders.')

    @classmethod
    @DBConnection().cursor_add
    def _get_deleted_suborders_rows(cls, cursor) -> json:
        headers = SubOrdersTable()._get_suborders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == True)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)


#Не использовать, до конца не реализован.
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
        






