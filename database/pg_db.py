from bs4 import BeautifulSoup as bs
import psycopg2
import os
from dotenv import load_dotenv
from pypika import Query, Table, Case, functions as fn
from datetime import datetime
import json
from typing import Dict, Any
import requests

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
        print("Таблицы успешно созданы")

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

    def get_orders_table(self) -> JsonDict:
        """Полная выгрузка"""
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(self.table).select(self.table.star)\
            .where(self.table.deleted == False)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [{k: v for k, v in zip(headers, row)} for row in orders]
        self.conn.close()
        return json.dumps(result, default=str)

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
                result = [{k: v for k, v in zip(headers, row)} for row in orders]
        self.conn.close()
        print(result)
        return json.dumps(result, default=str)

    def get_orders_table(self) -> JsonDict:
        """Полная выгрузка"""
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(self.table).select(self.table.star)\
            .where(self.table.deleted == False)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [{k: v for k, v in zip(headers, row)} for row in orders]
        self.conn.close()
        return json.dumps(result, default=str)

    def _get_deleted_orders_rows(self) -> JsonDict:
        headers = OrdersTable()._get_orders_header()
        q = Query.from_(self.table).select(self.table.star)\
            .where(self.table.deleted == True)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [{k: v for k, v in zip(headers, row)} for row in orders]
        self.conn.close()
        return json.dumps(result, default=str)

    def get_orders_report_data(self) -> JsonDict:
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
        q = Query.from_(self.table).select(*headers)\
            .where(self.table.deleted == False)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                orders = cursor.fetchall()
                result = [{k: v for k,v in zip(headers, row)} for row in orders]
        cursor.close()
        return json.dumps(result)

    def add_order(self, row: JsonDict) -> None:
        table = Table("orders")
        row = json.loads(row)
        row['approving_date'] = datetime.strptime(row['approving_date'], "%d.%m.%Y").date()
        row['deadline'] = datetime.strptime(row['deadline'], "%d.%m.%Y").date()
        _columns = row.keys()
        q = Query.into(table).columns(*_columns).insert(*row.values())
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        print(f"Поручение добавлено")

    def delete_order_row(self, id: bytes) -> None:
        """
        Данный метод сначала помечает удаленным конкретный приказ по id,
        далее все его подзадачи.
        """
        id = id.decode('utf-8')
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
                print(f'Подзадачи по id {id} не заведены')
        self.conn.close()
        print(f'Задача с id {id} и ее подзадачи "удалены" из orders.')

    def update_order(self, data: JsonDict) -> None:
        #Обязательно должен быть передан id записи
        data = json.loads(data)
        q = Query.update(self.table).where(self.table.id == data['id'])\
            .set('update_date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        for key in data:
            q = q.set(key, data[key])
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        print(f'Успешно обновленны данные id:{data["id"]}')


class SubOrdersTable(BaseDB):
    """
    Работа с подзадачами в поручении/приказе
    """
    table = Table('suborders')

    def _get_suborders_header(self):
        #Возвращает все имена столбцов таблицы SUBORDERS
        with self.conn:
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'suborders' ORDER BY ordinal_position;")
                    headers = [row[0] for row in cursor.fetchall()]
                    return headers
                except:
                    return None
                finally:
                    cursor.close()

    def get_suborders_table(self, id_orders: bytes) -> json:
        # Выгрзука подзадач по отдельному приказу или поручению
        # id_orders = id_orders.decode('utf-8')
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
                result = [{k: v for k, v in zip(headers, row)} for row in suborders]
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

                if all([True if row[0] == 'Завершено' else False for row in cursor.fetchall()]):
                    OrdersTable().update_order(json.dumps({
                        'status_code': 'Завершено',
                        'id': order_id
                    }))
                else:
                    OrdersTable().update_order(json.dumps({
                        'status_code': 'На исполнении',
                        'id': order_id
                    }))
        self.conn.close()

    def update_suborder(self, data: JsonDict) -> None:
        #Обязательно должен быть передан id записи и id_orders
        data = json.loads(data)
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
        print(f'Успешно обновленны данные id:{data["id"]}')

    def add_suborder(self, row: JsonDict) -> None:
        row = json.loads(row)
        _columns = row.keys()
        q = Query.into(self.table).columns(*_columns).insert(*row.values())
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        SubOrdersTable()._check_open_close_suborder(row['id_orders'])
        print(f"Поручение добавлено")

    def delete_suborder_row(self, order_id: bytes, suborder_id: str) -> None:
        #? шляпа с хинтами
        q = Query.update(self.table).where(self.table.id == suborder_id)\
            .set('deleted', True)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
        self.conn.close()
        SubOrdersTable()._check_open_close_suborder(order_id)
        print(f'Строка с id {suborder_id} "удалена" из suborders.')


class Users(BaseDB):

    table = Table('users')

    def __init__(self):
        super().__init__()

    @staticmethod
    def get_phone_book() -> dict:
        """
        Тянет данные с портала
        """
        # phonebook = {}
        phonebook = []
        r = requests.get('http://portal/phonebook')
        soup = bs(r.text, "html.parser")
        main_table = soup.find_all('tr', class_='usTblContent')
        for table in main_table:
            table = tuple(map(lambda x: x.text.replace('\n', ''), table))
            if table[9]:
                phonebook.append({
                    "user_name": table[3],
                    # 'position': table[5],
                    'email': table[9],
                    # 'phone': table[11] or '-',
                })
            else:
                continue
        return phonebook

    def add_user(self, user: bytes) -> None:
        user = json.loads(user)
        _columns = user.keys()
        q = Query.into(self.table).columns(*_columns).insert(*user.values())
        with self.conn:
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute(str(q))
                except psycopg2.errors.UniqueViolation as e:
                    print(f'Пользватель {user["user_name"]} уже имеется в базе.')
        self.conn.close()

    def get_users(self) -> JsonList:
        q = Query.from_(self.table).select(self.table.user_name)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                result = [user_name[0] for user_name in cursor.fetchall()]
        self.conn.close()
        return json.dumps(result)

    def get_user_mails(self) -> JsonDict:
        q = Query.from_(self.table).select(self.table.star)
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(str(q))
                result = [{user_name: email} for user_name, email in cursor.fetchall()]
        self.conn.close()
        return json.dumps(result)

    def update_users_table(self):
        phonebook = Users.get_phone_book()
        for row in phonebook:
            _columns = row.keys()
            q = Query.into(self.table).columns(*_columns).insert(*row.values())
            with self.conn:
                with self.conn.cursor() as cursor:
                    try:
                        cursor.execute(str(q))
                    except psycopg2.errors.UniqueViolation as e:
                        print(f'Пользватель {row["user_name"]} уже имеется в базе.')
        self.conn.close()

        print(f"Таблица пользователей обновлена")


if __name__ == "__main__":
    # BaseDB().create_tables()
    # Users().update_users_table()
    print(Users().get_users())
    add_order_row = json.dumps({
        'issue_type': 'Приказ',
        'issue_idx': '586',
        'approving_date': '19.07.2022',
        'title': "Об актуализации плана  реализации проекта  по использованию биометрической идентификации при обслуживании физических лиц",
        'initiator': 'Сергунина Е.В.',
        'approving_employee':'Терехина Е.С.',
        'deadline': '28.08.2022',
        'status_code': 'В работе',
        'comment': 'Приказ разбит на несколько задач',
        'reference': r'C:\Users\sidorovich_ns\Desktop\Projects\accounting_of_orders\income\Приказ_продажа монет кассовым работником.doc',
    })
    update_order_row = json.dumps({
        'id': '73c823aa-0310-40ae-bd2f-af3010498f44',
        'title': "Об актуализации плана  реализации проекта  по использованию биометрической идентификации при обслуживании физических лиц",
        'comment': 'Обновлено 01.09.2022',
        'deadline': '01.09.2022',
    })
    id_order = '41510fef-e109-4b54-93aa-db8b3bdeba3e'.encode('utf-8')
        # OrdersTable().add_order(add_order_row)
        # print(OrdersTable().get_orders_table())
        # print(OrdersTable()._get_orders_header())
    # OrdersTable().update_order(update_order_row)
    # print(OrdersTable()._get_deleted_orders_rows())

    add_suborder_row = json.dumps({
        'id_orders': id_order.decode('utf-8'),
        'employee': "Иванов И.И.",
        'deadline': '10.09.2022',
        'content': '8.Внести дополнение в Приложение к Учетной политике Банка «Положение о порядке ведения бухгалтерского учета операций с памятными и инвестиционными монетами», утвержденное Приказом № 1365/1 от 14.12.2016.',
        'status_code': 'В работе',
        'comment': 'Новая подзадача',
    })
    update_suborder_row = json.dumps({
        'id_orders': '41510fef-e109-4b54-93aa-db8b3bdeba3e',
        'id': '74e9fe3f-2ef5-4c35-9310-17cea65ad0dd',
        'content': 'Обновленное содержание',
        'comment': 'Обновлено 01.09.2022',
        'deadline': '01.09.2022',
    })
    suborder_id = '85657f88-07c4-49e5-a450-eaf6bb6d1d6b'

    # SubOrdersTable().delete_suborder_row(id_order.decode('utf-8'), suborder_id)
    # SubOrdersTable().add_suborder(add_suborder_row)
    # SubOrdersTable().update_suborder(update_suborder_row)