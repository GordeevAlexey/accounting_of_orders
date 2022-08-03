import sqlite3
from functools import wraps
from pypika import Query, Table, Field
from uuid import uuid4

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
    def _create_tables(cls, cursor):
        with open('database\schema.sql', 'r', encoding='utf-8') as query:
            tables_creation_request = query.read()
        cursor.executescript(tables_creation_request)
        cursor.close()

    @classmethod
    @cursor_add
    def get_orders(cls, cursor):
        table = Table('ORDERS')
        q = Query.from_(table).select(table.star)
        cursor.execute(str(q))
        result = cursor.fetchall()
        cursor.close()
        return result

    @classmethod
    @cursor_add
    def add_order(cls, cursor, *args):
        table = Table('ORDERS')
        q = Query.into(table).insert(uuid4(), *args)
        cursor.execute(str(q))
        cursor.close()
        print(f"Поручение добавлено")

    @classmethod
    @cursor_add
    def execute_query(cls, cursor, query):
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result


class FetchDataFormatter:
    pass

