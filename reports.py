import xlsxwriter
from io import BytesIO
from database.pg_db import OrdersTable, SubOrdersTable
import json
from datetime import datetime, timedelta
from pypika import Query, Table, Case, functions as fn
from database.utils import *
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.styles import NamedStyle
from send_email import Email


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


class ExecutedOfThePeriodData:
    """
    Осуществляет выборку исполненных ВРД за период из БД
    """
    def __init__(self, start_period: datetime, end_period: datetime):
        self.start_period = start_period
        self.end_period = end_period

    def get_executed_orders(self):
        orders_table = Table('orders')
        suborders_table = Table('suborders')
        q = Query.from_(suborders_table).select(
            suborders_table.id_orders,
            suborders_table.content,
            suborders_table.deadline,
            suborders_table.status_code,
            suborders_table.comment
        ).where(
            (suborders_table.deleted == False) &
            (suborders_table.close_date[self.start_period:self.end_period])
        )
        result = SubOrdersTable().execute_query(str(q))
        print(result)


class ExecutedOfThePeriod:
    def __init__(self, start_period: datetime, end_period: datetime, wb: Workbook) -> None:
        self.start_period = start_period
        self.end_period = end_period
        self.wb = wb
        self.wb.create_sheet("Исполненные за период")
    
    def _data_to_sheet(self) -> None:
        pass

    def _apply_styles(self) -> None:
        pass

    def form(self) -> bytes:
        pass


class ApprovedPeriodData:
    """
    Осуществляет выборку утвержденных ВРД за период из БД
    """
    def __init__(self, start_eriod: datetime, end_period: datetime) -> None:
        self.start_report_period = start_eriod
        self.end_report_period = end_period

    def _get_orders(self) -> list[ReportRow]:
        orders_table = Table('orders')
        q = Query.from_(orders_table).select(
                orders_table.id,
                orders_table.issue_type,
                orders_table.issue_idx,
                orders_table.approving_date,
                orders_table.title,
                orders_table.initiator,
                orders_table.approving_employee,
                orders_table.employee,
                orders_table.deadline,
                orders_table.status_code,
                orders_table.comment
        ).where(
            orders_table.approving_date[self.start_report_period:self.end_report_period]
        )
        orders = [ReportRow(*row) for row in OrdersTable().execute_query(str(q))]
        return orders

    def report_rows(self) -> list[ReportRow]:
        orders = self._get_orders()
        orders_ids = [row.id for row in orders]
        suborders_table = Table("suborders")
        q = Query.from_(suborders_table).select(
                suborders_table.content,
                suborders_table.deadline,
                suborders_table.status_code,
                suborders_table.comment
        ).where(
            (suborders_table.id_orders.isin(orders_ids)) &
            (suborders_table.deleted == False)
        )
        suborders = SubOrdersTable().execute_query(str(q))
        report_rows = []
        for order in orders:
            report_rows.append(order)
            for suborder in suborders:
                report_rows.append(
                    ReportRow(
                        title=suborder[0], deadline=suborder[1],
                        status_code=suborder[2], comment=suborder[3],
                        issue_type='Поручение', issue_idx=order.issue_idx,
                        id=None, approving_date=None, initiator=None,
                        approving_employee=None, employee=order.employee
                        )
                )
        return report_rows


class ApprovedForThePeriod:
    """
    Отчет об утвержденных за период ВРД
    """

    header = (
       'Вид поручения',
       '№',
       'Дата утверждения',
       'Тема',
       'Инициатор',
       'Утверждающий руководитель',
       'Ответственные исполнители',
       'Срок исполнения',
       'Статус поручения',
       'Содержание поручения',
       'Дата закрытия',
       'Примечание',
    )
    header_width = (17, 13, 23, 43, 40, 40, 40, 18, 45, 40, 18, 35)

    def __init__(self, start_period: datetime, end_period: datetime, wb: bytes) -> None:
        self.output = BytesIO()
        self.apd = ApprovedPeriodData(start_period, end_period)
        self.srp = datetime.strptime(start_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.erp = datetime.strptime(end_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.rows = self.apd.report_rows()
        # self.wb = Workbook()
        self.wb = load_workbook(wb)
        self.ws = self.wb.active
        self.ws.title = "Утвержденные за период"

    def _data_to_sheet(self):
        self.ws["A1"] = f"Внутренние распорядительные документы, утвержденные в период с {self.srp} по {self.erp}"
        self.ws["B2"] = '- без установленных сроков'
        self.ws["B3"] = '- на исполнении'
        self.ws["B4"] = '- исполнени'
        self.ws['B5'] = None
        self.ws.append(self.header)
        [self.ws.append(row[1:]) for row in self.rows]

        for col in [f'C7:C{self.ws.max_row}', f'H7:H{self.ws.max_row}', f'K7:K{self.ws.max_row}']:
            for cell in self.ws[col]:
                cell[0].style = NamedStyle(name='datetime', number_format='DD.MM.YYYY')

    def _apply_styles(self):
        #TODO: разукрасить по статусу исполнения
        self.ws.merge_cells('A1:L1')
        self.ws['A1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.ws['A1'].font = Font(name='Times New Roman', size=12, bold=True)
        self.ws.auto_filter.ref = "A6:L6"
        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        
        for cell in ('A2', 'A3', 'A4'):
            self.ws[cell].border = border
        self.ws['A2'].fill = PatternFill(fill_type='solid', fgColor="D7E4BC")
        self.ws['A3'].fill = PatternFill(fill_type='solid', fgColor="E6B9B8")
        self.ws['A4'].fill = PatternFill(fill_type='solid', fgColor="8DB4E3")

        for cell in self.ws['6:6']:
            cell.fill = PatternFill(fill_type='solid', fgColor="DBE5F1")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.font = Font(name='Times New Roman', size=12, bold=True)
            cell.border = border
            
        for row in self.ws.iter_rows(min_row=7):
            for col_idx, cell in enumerate(row, 1):
                self.ws.column_dimensions[get_column_letter(col_idx)].width = self.header_width[col_idx - 1] 
                cell.font = Font(name='Times New Roman', size=12, bold=False)
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                cell.border = border

    def form(self) -> bytes:
        self._data_to_sheet()
        self._apply_styles()
        self.wb.save(self.output)
        return self.output.getvalue()

class WeeklyReport:
    def __init__(self) -> None:
        #TODO Не забыть расскоментить)
        # self.report_date= datetime.today()
        # if self.report_date.weekday() == 4:
        #     self.end_report_period = self.report_date - timedelta(days=14)
        #     self.start_report_period = self.end_report_period - timedelta(days=4)
        # else:
        #     self.start_report_period = self.end_report_period = None
        self.start_report_period = "2022-11-09"
        self.end_report_period = "2022-11-11"
        self.output = BytesIO()
        self.wb = Workbook()

    def form_approved_for_the_period(self) -> None:
        self.wb.save(self.output)
        approved_period = ApprovedForThePeriod(
            self.start_report_period,
            self.end_report_period,
            self.output.getvalue()).form()
        self.wb = load_workbook(approved_period)

    def form_executed_for_the_period(self) -> bytes:
        return ExecutedOfThePeriod(
            self.start_report_period,
            self.end_report_period,
            self.wb
        ).form()

    def send_report(self) -> None:
        Email.send_weekly_report(
            f"""Отчет об исполнении за период {self.srp} - {self.erp}\n\n"""
            """*Данное сообщение сформированно автоматическе. Не нжуно на него отвечать.\n\n""",
            f"weekly_report {self.srp}-{self.erp}",
            self.form_executed_for_the_period()
        )

# WeeklyReport().send_report()
ExecutedOfThePeriodData("2022-11-09", "2022-11-11").get_executed_orders()