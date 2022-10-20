from ast import Or
import sqlite3
from functools import wraps
from pypika import Query, Table, Case, functions as fn
from uuid import uuid4
from datetime import datetime
import json
import pandas as pd
from datetime import datetime, timedelta
import io

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
    def execute_query(cls, cursor, query: str):
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result


class OrdersTable(DBConnection):
    """
    Работа с таблицей Поручений
    """

    table = Table("ORDERS")
    table_sub_orders = Table("SUBORDERS")
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
    def get_orders_table_pg_bar(cls, cursor) -> json:
        # Полная выгрузка плюс инфа для прогресс бара
        headers = OrdersTable()._get_orders_header()
        headers.append("progress")
        q = Query.from_(cls.table)\
                 .select(cls.table.star,
                         (100
                         /
                         Query.from_(cls.table_sub_orders)
                                              .select(fn.Count(cls.table_sub_orders))
                                              .where((cls.table_sub_orders.id_orders == cls.table.id)
                                                    & (cls.table_sub_orders.deleted == False)))
                         *
                         Query.from_(cls.table_sub_orders)
                         .select(fn.Count(cls.table_sub_orders))
                         .where((cls.table_sub_orders.id_orders == cls.table.id)
                                & (cls.table_sub_orders.status_code == "Завершено")
                                & (cls.table_sub_orders.deleted == False))
                         )\
                 .where(cls.table.deleted == False)

        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k, v in zip(headers, row)} for row in orders]
        print(type(result))
        cursor.close()
        return json.dumps(result)

    @classmethod
    @DBConnection().cursor_add
    def get_orders_table(cls, cursor) -> json:
        #Полная выгрузка
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == False)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k, v in zip(headers, row)} for row in orders]
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
        result = [{k: v for k, v in zip(headers, row)} for row in orders]
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
        """
        Данный метод сначала помечает удаленным конкретный приказ по id,
        далее все его подзадачи.
        """
        id = id.decode('utf-8')
        q = Query.update(cls.table).where(cls.table.id == id)\
            .set('deleted', True)
        cursor.execute(str(q))
        q_s = Query.from_(SubOrdersTable.table).select(SubOrdersTable.table.id)\
            .where(
                (SubOrdersTable.table.id_orders == id) &
                (SubOrdersTable.table.deleted != True)
            )
        try:
            suborders_ids = SubOrdersTable().execute_query(str(q_s))
            for _id in suborders_ids:
                SubOrdersTable().delete_suborder_row(_id.encode('utf-8'))
        except:
            print(f'Подзадачи по id {id} не заведены')
        cursor.close()
        print(f'Задача с id {id} и ее подзадачи "удалены" из orders.')

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
        # Выгрзука подзадач по отдельному приказу или поручению
        # id_orders = id_orders.decode('utf-8')
        headers = SubOrdersTable()._get_suborders_header()
        headers.append('condition')
        q = Query.from_(cls.table).select(cls.table.star,
                                          Case().when(cls.table.status_code == "Завершено", True)\
                                          .else_(False))\
            .where((cls.table.deleted == False) & (cls.table.ID_ORDERS == id_orders))
        cursor.execute(str(q))
        suborders = cursor.fetchall()
        result = [{k: v for k, v in zip(headers, row)} for row in suborders]
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
        result = [{k: v for k, v in zip(headers, row)} for row in suborders]
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
        SubOrdersTable().check_open_close_suborder(row['id_orders'])
        print(f"Поручение добавлено")

    @classmethod
    @DBConnection().cursor_add
    def update_suborder(cls, cursor, data: json) -> None:
        #Обязательно должен быть передан id записи и id_orders
        data = json.loads(data)
        q = Query.update(cls.table).where(
            (cls.table.id == data['id'])
            & (cls.table.id_orders == data['id_orders'])
        ).set('update_date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        for key in data:
            q = q.set(key, data[key])
        cursor.execute(str(q))
        SubOrdersTable().check_open_close_suborder(data['id_orders'])
        #Проверка: если все подзадачи закрыты, то оснавная задача также автоматически закрывается
        #Проставляется в status_code значение 'Завершено'
        # id_orders_query = Query.from_(cls.table).select(cls.table.status_code)\
        #     .where(cls.table.id_orders == data['id_orders'])
        # cursor.execute(str(id_orders_query))
        # if all(
        #     [True if row[0] == 'Завершено' else False for row in cursor.fetchall()]
        # ):
        #     OrdersTable.update_order(json.dumps({
        #         'status_code': 'Завершено',
        #         'id': data['id_orders']
        #
        #     }))
        cursor.close()
        print(f'Успешно обновленны данные id:{data["id"]}')

    @classmethod
    @DBConnection().cursor_add
    def delete_suborder_row(cls, cursor, order_id, suborder_id) -> None:
        #id = id.decode('utf-8')
        q = Query.update(cls.table).where(cls.table.id == suborder_id)\
            .set('deleted', True)
        cursor.execute(str(q))
        cursor.close()
        SubOrdersTable().check_open_close_suborder(order_id)
        print(f'Строка с id {id} "удалена" из suborders.')

    @classmethod
    @DBConnection().cursor_add
    def _get_deleted_suborders_rows(cls, cursor) -> json:
        headers = SubOrdersTable()._get_suborders_header()
        q = Query.from_(cls.table).select(cls.table.star)\
            .where(cls.table.deleted == True)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k, v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)

    @classmethod
    @DBConnection().cursor_add
    def check_open_close_suborder(cls, cursor, order_id):

        id_orders_query = Query.from_(cls.table).select(cls.table.status_code)\
            .where((cls.table.id_orders == order_id) & (cls.table.deleted == False))
        cursor.execute(str(id_orders_query))

        #x = cursor.fetchall()

        if all([True if row[0] == 'Завершено' else False for row in cursor.fetchall()]):
            OrdersTable.update_order(json.dumps({
                'status_code': 'Завершено',
                'id': order_id
            }))
        else:
            OrdersTable.update_order(json.dumps({
                'status_code': 'На исполнении',
                'id': order_id
            }))


class Dumper:
    def create_dump(self) -> str:
        """
        Создает дамп базы и возрващает путь к нему
        """
        dump_path = 'backup.sql'
        conn = sqlite3.connect('database.db')  
        with io.open(dump_path, 'w') as p: 
            for line in conn.iterdump(): 
                p.write('%s\n' % line)
        print('Backup performed successfully!')
        print(f'Data Saved as {dump_path}')
        conn.close()
        return dump_path


#Не использовать, до конца не реализован.
class ReportDatabaseWriter(OrdersTable):

    table = Table("ORDERS")
    table_sub_orders = Table("SUBORDERS")

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

    """
    Возвращает информацию для формирования карточки для закрытия поручения. 
    """
    @classmethod
    @DBConnection().cursor_add
    def get_info(cls, cursor, uuid_suboder):
        headers = ["issue_type", "issue_idx", "approving_date", "title", "initiator", "approving_employee",
                   "deadline", "comment", "employee", "deadline_suborder", "status_code", "content", "comment_suborder"]
        q = Query\
            .from_(cls.table_sub_orders)\
            .join(cls.table)\
            .on(cls.table_sub_orders.id_orders == cls.table.id)\
            .select(cls.table.issue_type,
                    cls.table.issue_idx,
                    cls.table.approving_date,
                    cls.table.title,
                    cls.table.initiator,
                    cls.table.approving_employee,
                    cls.table.deadline,
                    cls.table.comment,
                    cls.table_sub_orders.employee,
                    cls.table_sub_orders.deadline,
                    cls.table_sub_orders.status_code,
                    cls.table_sub_orders.content,
                    cls.table_sub_orders.comment)\
            .where(cls.table_sub_orders.id == uuid_suboder)
        cursor.execute(str(q))
        orders = cursor.fetchall()
        result = [{k: v for k, v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)
