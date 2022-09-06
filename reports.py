from ast import Or
import xlsxwriter
from io import BytesIO
from database.db import OrdersTable, SubOrdersTable
import json
from datetime import datetime


#ПОКА ЭТОТ КЛАСС НЕ ИСПОЛЬЗОВАТЬ, ПОКА НЕ СОГЛАСЮТ ШАБЛОН ОТЧЕТА 01.09.2022
class OrderReport:
    #https://stackoverflow.com/questions/63465155/how-to-return-xlsx-file-from-memory-in-fastapi
    title = f'ВРД\n АО "БАНК АКЦЕПТ {datetime.now().year}"'
    header = {
       'issue_type': 'Вид поручения',
       'issue_idx': '№',
       'approving_date': 'Дата утверждения',
       'title': 'Тема',
       'initiator': 'Инициатор',
       'approving_employee': 'Утверждающий руководитель',
       'employee': 'Ответственные исполнители',
       'deadline': 'Срок исполнения',
       'content': 'Содержание поручения',
       'performance_note': 'Отметка об исполнении',
       'status_code': 'Статус поручения',
       'closa_date': 'Дата закрытия',
       'comment': 'Примечание',
    }
    header_width = (12, 18, 18, 20, 20, 17, 14, 13, 29, 18, 18, 18, 18,)

    def __init__(self):
        self.output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output)
        self.worksheet = self.workbook.add_worksheet('Краткосрочные документы')
        self.title_merge_format = self.workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
        })
        self.header_format = self.workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#dce6f1',
                'text_wrap': 'true'
        })
        self.cell_format = self.workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': 'true'
        })

    def _create_template(self) -> None:
        self.worksheet.merge_range('A1:M3', self.title, self.title_merge_format)
        for col_idx, values in enumerate(zip(self.header.values(), self.header_width)):
            cell_value, width = values 
            self.worksheet.write(3, col_idx, cell_value, self.header_format)
            self.worksheet.set_column(col_idx, col_idx, width, self.cell_format)
        self.worksheet.autofilter('A4:M4')

    def _add_data_from_db(self) -> None:
        from pprint import pprint
        self._create_template()
        orders_rows = json.loads(OrdersTable().get_orders_report_data())
        pprint(orders_rows)

        orders_id = [row['id'] for row in orders_rows]
        suborders_rows = []

        for id in orders_id:
            suborders_rows.append(*json.loads(SubOrdersTable()\
                .get_suborders_report_data(id.encode('utf-8'))))
        print(suborders_rows)



        # for row_idx, row in enumerate(rows, 4):
        #     self.worksheet.write(row_idx, 0, row_idx - 3, self.cell_format)
        #     for col_idx, cell in enumerate(row.values()):
        #         self.worksheet.write(row_idx, col_idx + 1, cell, self.cell_format)
    
    def get_report(self) -> None:
        self._add_data_from_db()
        self.workbook.close()
        self.output.seek(0)



OrderReport()._add_data_from_db()