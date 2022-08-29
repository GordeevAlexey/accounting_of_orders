import xlsxwriter
from io import BytesIO
from database.db import OrdersTable
import json


class OrderReport:
    #https://stackoverflow.com/questions/63465155/how-to-return-xlsx-file-from-memory-in-fastapi
    title = 'ЖУРНАЛ УЧЕТА И КОНТРОЛЯ ИСПОЛНЕНИЯ  ВНУТРЕННИХ РАСПОРЯДИТЕЛЬНЫХ ДОКУМЕНТОВ АО "БАНК АКЦЕПТ"'
    header = (
        'Вид поручения',
        '№',
        'Дата утверждения поручения',
        'Тема',
        'Инициатор',
        'Утверждающий руководитель',
        'Ответстченные исполнители',
        'Срок исполнения',
        'Статус поручения',
        'Дата закрытия',
        'Примечание',
    )
    header_width = (12, 18, 18, 20, 20, 17, 14, 13, 29)

    def __init__(self):
        self.output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output)
        self.worksheet = self.workbook.add_worksheet('Краткосрочные документы')
        self.title_merge_format = self.workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#00fffb'
        })
        self.header_format = self.workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#c9c9d1',
                'text_wrap': 'true'
        })
        self.cell_format = self.workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': 'true'
        })

    def _create_template(self) -> None:
        self.worksheet.merge_range('A1:I3', self.title, self.title_merge_format)
        for col_idx, values in enumerate(zip(self.header, self.header_width)):
            cell_value, width = values 
            self.worksheet.write(3, col_idx, cell_value, self.header_format)
            self.worksheet.set_column(col_idx, col_idx, width, self.cell_format)
        self.worksheet.autofilter('A4:I4')

    def _add_data_from_db(self) -> None:
        self._create_template()
        rows = json.loads(OrdersTable().get_orders_report_data())
        for row_idx, row in enumerate(rows, 4):
            self.worksheet.write(row_idx, 0, row_idx - 3, self.cell_format)
            for col_idx, cell in enumerate(row.values()):
                self.worksheet.write(row_idx, col_idx + 1, cell, self.cell_format)
    
    def get_report(self) -> None:
        self._add_data_from_db()
        self.workbook.close()
        self.output.seek(0)

r = OrderReport()._add_data_from_db()

# data = json.dumps({
#     'id': 'a79929c3-7aa6-475b-9267-87f3a39fc9e0',
#     'issue_type': 'Приказ',
#     'initiator': 'Сидорович Н.С.',
#     'title': 'О запуске пилотного проекта...',
#     'issue_date': '22.08.2022',
#     'employee': 'Захаров С.А.',
#     'status_code': 'Заведено',
#     'close_date': None,
#     'comment': 'Срочно',
# })
# DBConnection.update_order(data)
# print(DBConnection.get_orders())
