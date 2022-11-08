import json
import pandas as pd
from database.db import DBConnection, DBConnector, OrdersTable
from database.ibso import Employees
# tb = OrdersTable()
# print(tb.get_orders_table())
#
# tb.add_order(json.dumps({'issue_type': 'Приказ',
#               'issue_idx': '652',
#               'title': 'Об использовании чего-то',
#               'initiator': 'Иванов Иван Иванович',
#               'approving_employee': 'Иванов Иван Иванович',
#               'deadline': '01.09.2022',
#               'status_code': 'На исполнении',
#               }))

DBConnection()._create_tables("./database/sql/pg_schema.sql")

# x = json.loads(Employees.get_phone_book())['Архив']
# x = pd.DataFrame(json.loads(Employees.get_phone_book()).keys())

x = json.loads(Employees.get_phone_book_for_selected())

print(x)
