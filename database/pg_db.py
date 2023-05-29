import psycopg2
import os
from dotenv import load_dotenv
from pypika import Query, Table, Case, functions as fn
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional
from database.utils import User, date_formatter
import logging
from logger.logger import *
from database.ibso import get_users_and_emails


logger = logging.getLogger(__name__)


#Алиас для json
JsonDict = Dict[str, Any]
JsonList = [Any]


load_dotenv()

class BaseDB:
    def __init__(self):
        self.user = os.getenv("USER")
        self.dbname = os.getenv("DBNAME")
        self.password = os.getenv("PASSWORD")
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")
        self.conn = psycopg2.connect(
            # async_=True, если стоит этот аргумент, что надо что-то сделать с коммитами
            user=self.user,
            dbname=self.dbname,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        self.conn.autocommit = True

    def create_tables(self):
        with open('database/sql/pg_schema.sql', 'r', encoding='utf-8') as query:
            tables_creation_request = query.read()
            with self.conn:
                with self.conn.cursor() as cursor:
                    cursor.execute(tables_creation_request)
            self.conn.close()
        logger.info("Таблицы успешно созданы")
        

    def execute_query(self, query: str):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
        self.conn.close()
        return result


class OrdersTable(BaseDB):
    """
    Работа с таблицей Поручений
    """

    table = Table("orders")
    table_sub_orders = Table("suborders")

    def __init__(self) -> None:
        super().__init__()

    def _get_orders_header(self):
        """
        В озвращает все имена столбцов таблицы ORDERS
        """
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders' ORDER BY ordinal_position;")
                    headers = [row[0] for row in cursor.fetchall()]
            return headers
        except:
            return None
        finally:
            cursor.close()

    def get_orders_table_pg_bar(self) -> json:
        """
         Полная выгрузка плюс инфа для прогресс бара
        """
        headers = OrdersTable()._get_orders_header()
        headers.append("progress")
        q = Query.from_(self.table)\
                 .select(self.table.star,
                         (100
                         /
                         Query.from_(self.table_sub_orders)
                                              .select(fn.NullIf(fn.Count(self.table_sub_orders), 0))
                                              .where((self.table_sub_orders.id_orders == self.table.id)
                                                     & (self.table_sub_orders.deleted == False)))
                         *
                         Query.from_(self.table_sub_orders)
                         .select(fn.NullIf(fn.Count(self.table_sub_orders), 0))
                         .where((self.table_sub_orders.id_orders == self.table.id)
                                & (self.table_sub_orders.status_code == "Завершено")
                                & (self.table_sub_orders.deleted == False))
                         )\
                 .where(self.table.deleted == False)

        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [dict(zip(headers, row)) for row in orders]
                result = list(map(date_formatter, result))
        self.conn.close()
        return json.dumps(result, default=str)

    def get_orders_table(self) -> JsonList:
        """Полная выгрузка"""
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(self.table).select(self.table.star)\
            .where(self.table.deleted == False)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [dict(zip(headers, row)) for row in orders]
                result = list(map(date_formatter, result))
        self.conn.close()
        return json.dumps(result, default=str)

    def _get_deleted_orders_rows(self) -> JsonList:
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(self.table).select(self.table.star)\
            .where(self.table.deleted == True)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [dict(zip(headers, row)) for row in orders]
                result = list(map(date_formatter, result))
        self.conn.close()
        return json.dumps(result, default=str)

    def get_orders_report_data(self) -> JsonList:
        #Выгрузка по форме отчета
        headers = (
            'id',
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
        q = Query.from_(self.table).select(*headers)\
            .where(self.table.deleted == False)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [dict(zip(headers, row)) for row in orders]
                result = list(map(date_formatter, result))
        cursor.close()
        return json.dumps(result)

    def add_order(self, row: JsonDict) -> None:
        table = Table("orders")
        if not row['deadline']:
            row['deadline'] = datetime.now().date().replace(month=12, day=31)
        row['approving_date'] = datetime.strptime(row['approving_date'], "%Y-%m-%d").date()
        row['deadline'] = datetime.strptime(row['deadline'], "%Y-%m-%d").date()
        _columns = row.keys()
        q = Query.into(table).columns(*_columns).insert(*row.values())
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        logger.info("Поручение добавлено")

    def delete_order_row(self, id: bytes) -> None:
        """
        Данный метод сначала помечает удаленным конкретный приказ по id,
        далее все его подзадачи.
        """
        # id = id.decode('utf-8')
        q = Query.update(self.table).where(self.table.id == id)\
            .set('deleted', True)

        with self.conn:
            with self.conn.cursor() as cursor:
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
                logger.info(f'Подзадачи по id {id} не заведены')
        self.conn.close()
        logger.info(f'Задача с id {id} и ее подзадачи "удалены" из orders.')

    def update_order(self, data: dict) -> None:
        #Обязательно должен быть передан id записи
        q = Query.update(self.table).where(self.table.id == data['id'])\
            .set('update_date', datetime.now())
        for key in data:
            q = q.set(key, data[key])
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        logger.info(f'Успешно обновленны данные id:{data["id"]}')


class SubOrdersTable(BaseDB):
    """
    Работа с подзадачами в поручении/приказе
    """
    table = Table('suborders')

    def _get_suborders_header(self) -> Optional[list]:
        #Возвращает все имена столбцов таблицы SUBORDERS
        with self.conn:
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'suborders' ORDER BY ordinal_position;")
                    return [row[0] for row in cursor.fetchall()]
                except:
                    return None

    def get_suborders_table(self, id_orders: str) -> json:
        # Выгрзука подзадач по отдельному приказу или поручению
        headers = SubOrdersTable()._get_suborders_header()
        headers.append('condition')
        q = Query.from_(self.table).select(self.table.star,
                                           Case().when(self.table.status_code == "Завершено", True)\
                                           .else_(False))\
            .where((self.table.deleted == False) & (self.table.id_orders == id_orders))
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                suborders = cursor.fetchall()
                result = [dict(zip(headers, row)) for row in suborders]
                result = list(map(date_formatter, result))
                cursor.close()

        return json.dumps(result, default=str)

    def _check_open_close_suborder(self, order_id: str):
        """
        Проверка: если все подзадачи закрыты, то оснавная задача также автоматически закрывается
        Проставляется в status_code значение 'Завершено'
        """
        id_orders_query = Query.from_(self.table).select(self.table.status_code)\
            .where((self.table.id_orders == order_id) & (self.table.deleted == False))
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(id_orders_query))

                if all(row[0] == 'Завершено' for row in cursor.fetchall()):
                    OrdersTable().update_order({
                        'status_code': 'Завершено',
                        'id': order_id
                    })
                else:
                    OrdersTable().update_order({
                        'status_code': 'На исполнении',
                        'id': order_id
                    })
        self.conn.close()

    def check_for_update(self, data_for_update: dict) -> JsonDict:
        """
        Функция проверяет какие данные в таблице suborders подлежат обновлению
        и пишет их в таблицу history 
        """
        data_to_update = {
            "id_orders": data_for_update['id_orders'],
            "id": data_for_update['id'],
        }
        table_data = json.loads(SubOrdersTable().get_suborders_table(data_for_update['id_orders']))[0]

        if data_for_update['employee'] != table_data['employee']:
            data_to_update["employee"] = data_for_update['employee']

        if data_for_update['deadline'] != table_data['deadline']:
            data_to_update["deadline"] = data_for_update['deadline']

        if data_for_update['content'] != table_data['content']:
            data_to_update["content"] = data_for_update['content']

        return data_to_update

    def close_suborder(self, row: dict) -> None:

        q = Query.update(self.table).where(
            (self.table.id == row['id']) &
            (self.table.id_orders == row['id_orders'])
        ).set('update_date', datetime.now())\
         .set('close_date', datetime.now())\
         .set('status_code', 'Завершено')
        for key in row:
            q = q.set(key, row[key])

        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        SubOrdersTable()._check_open_close_suborder(row['id_orders'])

    def update_suborder(self, data: dict) -> None:
        #Обязательно должен быть передан id записи и id_orders
        _id = data['id']
        q = Query.update(self.table).where(
            (self.table.id == data['id'])
            & (self.table.id_orders == data['id_orders'])
        ).set('update_date', datetime.now())
        for key in data:
            q = q.set(key, data[key])
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        SubOrdersTable()._check_open_close_suborder(data['id_orders'])
        self.conn.close()
        HistoryTable().add(self.check_for_update(data))
        logger.info(f'Успешно обновленны данные id:{_id}')

    def add_suborder(self, row: dict) -> str:
        """
        Возвращает созданный id подзадачи
        """
        _columns = row.keys()
        if not row['deadline']:
            row['deadline'] = datetime.now().date().replace(month=12, day=31)
        q = Query.into(self.table).columns(*_columns).insert(*row.values())
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q) + "RETURNING id")
                [suborder_id] = cursor.fetchone()
        self.conn.close()
        SubOrdersTable()._check_open_close_suborder(row['id_orders'])
        logger.info("Поручение добавлено")
        return suborder_id

    def delete_suborder_row(self, order_id: str, suborder_id: str) -> None:
        q = Query.update(self.table).where(self.table.id == suborder_id)\
            .set('deleted', True)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        SubOrdersTable()._check_open_close_suborder(order_id)
        logger.info(f'Строка с id {suborder_id} "удалена" из suborders.')

    async def get_delay_suborders(self, days: int = 0) -> dict[str, str] | None:
        """
        Возвращает выборку по просроченным поручениям.
        """
        delay_date = datetime.now() + timedelta(days=days)
        cols = (
            'id',
            'employee',
        )
        q = Query.from_(self.table).select(*cols)\
            .where(
                (self.table.deleted == False) & (self.table.status_code != 'Завершено')
                & (self.table.deadline == delay_date.strftime('%Y-%m-%d'))
            )
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                suborders = cursor.fetchall()
        self.conn.close()
        if suborders:
            suborders = [dict(zip(cols, row)) for row in suborders]
            suborders = list(map(date_formatter, suborders))
            for order in suborders:
                users = await UsersTable().select_users(order['employee'].split(", "))
                order.update({'employee': users})
        else:
            suborders = None
        return suborders


class HistoryTable(BaseDB):
    table = Table('history')

    def __init__(self):
        super().__init__()

    def add(self, row: JsonDict) -> None:
        cheсk_id_relation = row.get('id_orders')

        match cheсk_id_relation:
            case None:
                id_orders = row.get('id')
                id_suborders = None
            case _:
                id_orders = cheсk_id_relation
                id_suborders = row.get('id')
                del row['id_orders']
        del row['id']

        q = Query.into(self.table).columns(
            self.table.id_orders,
            self.table.id_suborders,
            self.table.data,
            ).insert(id_orders, id_suborders, json.dumps(row))
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()


class UsersTable:

    async def select_users(self, users: list[str]) -> list[User]:
        """
        Возвращает список именованный кортежей с именем пользователя и его почтой
        """
        users_emails = await get_users_and_emails()
        return [User(**d) for d in users_emails if d['user_name'] in users]

    async def get_users(self) -> JsonList:
        users_emails = await get_users_and_emails()
        result = [d['user_name'] for d in users_emails]
        return json.dumps(sorted(result))


class Reports(BaseDB):
    table_orders = Table('orders')
    table_sub_orders = Table('suborders')

    def __init__(self):
        super().__init__()

    def get_info_suborder(self, id_suborder: str) -> JsonDict:
        headers = ("id_order", "issue_type", "issue_idx", "approving_date", "title",
                   "initiator", "approving_employee",
                   "employee_order", "deadline", "comment", "reference",
                   "id_suborder", "employee_sub_order", "deadline_suborder",
                   "status_code", "content", "comment_suborder")
        q = Query\
            .from_(self.table_sub_orders)\
            .join(self.table_orders)\
            .on(self.table_sub_orders.id_orders == self.table_orders.id)\
            .select(self.table_orders.id,
                    self.table_orders.issue_type,
                    self.table_orders.issue_idx,
                    self.table_orders.approving_date,
                    self.table_orders.title,
                    self.table_orders.initiator,
                    self.table_orders.approving_employee,
                    self.table_orders.employee,
                    self.table_orders.deadline,
                    self.table_orders.comment,
                    self.table_orders.reference,
                    self.table_sub_orders.id,
                    self.table_sub_orders.employee,
                    self.table_sub_orders.deadline,
                    self.table_sub_orders.status_code,
                    self.table_sub_orders.content,
                    self.table_sub_orders.comment)\
            .where(self.table_sub_orders.id == id_suborder)

        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()

        result = [dict(zip(headers, row)) for row in orders]
        self.conn.close()
        return json.dumps(result, default=str)

