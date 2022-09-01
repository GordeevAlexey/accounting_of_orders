from db import *
import json


add_order_row = json.dumps({
    'issue_type': 'Приказ',
    'issue_idx': '586',
    'approving_date': '19.07.2022',
    'title': "Об актуализации плана  реализации проекта  по использованию биометрической идентификации при обслуживании физических лиц",
    'initiator': 'Сергунина Е.В.',
    'approving_employee':'Терехина Е.С.',
    'deadline': '28.08.2022',
    'performance_note': None,
    'status_code': 'В работе',
    'close_date': '',
    'comment': 'Приказ разбит на несколько задач',
    'reference': r'C:\Users\sidorovich_ns\Desktop\Projects\accounting_of_orders\income\Приказ_продажа монет кассовым работником.doc',
})

#подставить свой id
updatte_order_row = json.dumps({
    'id': '7799e5a1-fccc-4134-bd06-7a0c1d9d17a8',
    'title': "Об актуализации плана  реализации проекта  по использованию биометрической идентификации при обслуживании физических лиц",
    'comment': 'Обновлено 01.09.2022',
    'deadline': '01.09.2022',
})

#подставить свой id_order
id_order = '7799e5a1-fccc-4134-bd06-7a0c1d9d17a8'.encode('utf-8')

add_suborder_row = json.dumps({
    'id_orders': id_order.decode('utf-8'),
    'employee': "Федоров А.И.",
    'deadline': '28.08.2022',
    'content': 'Регистрация заявки в ЦФТ для  подключения с использованием мобильного приложения банка',
    'performance_note': None,
    'status_code': 'В работе',
    'close_date': '04.09.2022',
    'comment': 'Подзадача',

})

update_suborder_row = json.dumps({
    'id_orders': '7799e5a1-fccc-4134-bd06-7a0c1d9d17a8',
    'id': '2220ab33-2fda-4843-89c1-92443b767dac',
    'content': 'Обновленное содержание',
    'comment': 'Обновлено 01.09.2022',
    'deadline': '01.09.2022',

})


class TestOrdersTable:
    def test_add_order(self):
        try:
            OrdersTable.add_order(add_order_row)
            print('test_add_order passed!')
        except:
            raise

    def test_get_orders_table(self):
        try:
            OrdersTable().get_orders_table()
            print('test_get_orders_table passed!')
        except:
            raise

    def test_get_orders_report_data(self):
        try:
            OrdersTable().get_orders_report_data()
            print('test_get_orders_report_data passed!')
        except:
            raise

    def test_update_order(self, data: json):
        try:
            OrdersTable().update_order(data)
            print('test_update_order passed!')
        except:
            raise

    def test_get_delay_orders(self, days: int = 0):
        try:
            print(OrdersTable().get_delay_orders())
            print('test_get_delay_orders passed!')
        except:
            raise


class TestSubOrdersTable:
    def test_add_suborder(self, row: json):
        try:
            SubOrdersTable.add_suborder(row)
            print('test_add_order passed!')
        except:
            raise

    def test_get_suborders_table(self, id_order: bytes):
        try:
            print(json.loads(SubOrdersTable().get_suborders_table(id_order)))
            print('test_get_orders_table passed!')
        except:
            raise

    def test_get_suborders_report_data(self, id_orders: bytes):
        try:
            print(json.loads(SubOrdersTable().get_suborders_report_data(id_orders)))
            print('test_get_orders_report_data passed!')
        except:
            raise

    def test_update_suborder(self, data: json):
        try:
            SubOrdersTable().update_suborder(data)
            print('test_update_order passed!')
        except:
            raise

    def test_get_delay_suborders(self, id_orders: bytes, days: int = 0):
        try:
            print(SubOrdersTable().get_delay_suborders(id_orders, days))
            print('test_get_delay_orders passed!')
        except:
            raise


if __name__ == "__main__":
    DBConnection()._create_tables('database\sql\schema.sql')
    TestOrdersTable.test_add_order(add_order_row)
    TestSubOrdersTable().test_add_suborder(add_suborder_row)
    TestSubOrdersTable().test_get_suborders_table(id_order)
    TestSubOrdersTable().test_get_suborders_report_data(id_order)
    TestSubOrdersTable().test_update_suborder(update_suborder_row)
    TestSubOrdersTable().test_get_delay_suborders(id_order)