import xlsxwriter
from io import BytesIO
from database.pg_db import OrdersTable, SubOrdersTable
import json
from datetime import datetime, timedelta
from pypika import Query, Table
from database.utils import *
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from send_email import Email
import psycopg2

    

SUBORDERS_HEADER = (
    "id_orders",
    "content",
    "deadline",
    "status_code",
    "employee",
    "comment",
    "close_date"
)

ORDERS_HEADER = (
    "id",
    "issue_type",
    "issue_idx",
    "approving_date",
    "title",
    "initiator",
    "approving_employee",
    "employee",
    "deadline",
    "status_code",
    "comment"
)

REPORT_HEADER = (
    'Вид поручения',
    '№',
    'Дата утверждения',
    'Тема',
    'Инициатор',
    'Утверждающий руководитель',
    'Ответственные исполнители',
    'Срок исполнения',
    'Содержание поручения',
    'Статус поручения',
    'Примечание',
)

REPORT_HEADER_WIDTH = (17, 13, 23, 43, 40, 40, 40, 18, 45, 40, 18, 35)

@dataclass(frozen=True, slots=True)
class SuborderRow:
    id_orders: str
    id: str
    employee: str | None
    deadline: str | None
    content: str | None


class ReportOrderRow(NamedTuple):
    id: Optional[str] = None
    issue_type: Optional[str] = None
    issue_idx: Optional[int] = None
    approving_date: Optional[datetime] = None
    title: Optional[str] = None
    initiator: Optional[str] = None
    approving_employee: Optional[str] = None
    employee: Optional[str] = None
    deadline: Optional[datetime] = None
    status_code: Optional[str] = None
    comment: Optional[str] = None


class ReportSuborderRow(NamedTuple):
    id: Optional[str] = None
    id_orders: Optional[str] = None
    content: Optional[str] =None
    deadline: Optional[datetime] = None
    status_code: Optional[str] = None
    employee: Optional[str] = None
    comment: Optional[str] = None
    close_date: Optional[str] = None
    

def rawrows_to_reportrows(headers: tuple, rows: list[tuple], row_type: Any) -> tuple[Any]:
    """
    Преобразует строки из бд в ReoportRow
    """
    rows = map(date_formatter, [{k: v for k, v in zip(headers, row)} for row in rows])
    rows = tuple(row_type(**row) for row in rows) 
    return rows

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
    Осуществляет выборку ВРД со сроками исполнения за период из БД
    """
    orders_table = Table('orders')
    suborders_table = Table('suborders')

    def __init__(self, start_period: datetime, end_period: datetime):
        self.start_period = start_period
        self.end_period = end_period

    def _get_executed_suborders(self) -> tuple[ReportOrderRow]:
        q = Query.from_(self.suborders_table).select(
            self.suborders_table.id_orders,
            self.suborders_table.content,
            self.suborders_table.deadline,
            self.suborders_table.status_code,
            self.suborders_table.employee,
            self.suborders_table.comment,
            self.suborders_table.close_date,
        ).where(
            (self.suborders_table.deleted == False) &
            (self.suborders_table.deadline[self.start_period:self.end_period])
        )
        suborders = rawrows_to_reportrows(SUBORDERS_HEADER, SubOrdersTable().execute_query(str(q)), ReportSuborderRow)
        return suborders

    def get_data(self) -> tuple[tuple[Any]]:
        suborders = self._get_executed_suborders()
        #Тут множество надо понаблюдать за порядком id_orders
        orders_id = {row.id_orders for row in suborders}
        q = Query.from_(self.orders_table).select(
                self.orders_table.id,
                self.orders_table.issue_type,
                self.orders_table.issue_idx,
                self.orders_table.approving_date,
                self.orders_table.title,
                self.orders_table.initiator,
                self.orders_table.approving_employee,
                self.orders_table.employee,
                self.orders_table.deadline,
                self.orders_table.status_code,
                self.orders_table.comment
        ).where(
            self.orders_table.id.isin(orders_id)
        )
        try:
            orders = rawrows_to_reportrows(ORDERS_HEADER, OrdersTable().execute_query(str(q)), ReportOrderRow)
        #тут надо что-то придумать, как доджить это исключение
        except psycopg2.errors.SyntaxError as e:
            print(f"Скорее всего за период {self.start_period} - {self.end_period} данных не найдено! Ошибка -> {str(e)}")
            # raise Exception(f"Скорее всего за период {self.start_period} - {self.end_period} данных не найдено! Ошибка -> {str(e)}")
        return orders, suborders


class ExecutedOfThePeriod:

    def __init__(self, start_period: datetime, end_period: datetime, wb: Workbook) -> None:
        self.start_period = start_period
        self.end_period = end_period
        self.srp = datetime.strptime(start_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.erp = datetime.strptime(end_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.wb = wb
        self.wb.create_sheet("Исполненные за период")
        self.ws = wb['Исполненные за период']

    def _fill_row(self, row_idx: int, row: Any) -> None:
        if row.status_code == "На исполнении":
            _fill = PatternFill(fill_type='solid', fgColor="E6B9B8")
            for col_idx in range(1, self.ws.max_column + 1):
                self.ws.cell(row_idx, col_idx).fill = _fill
    
    def _data_to_sheet(self) -> None:
        orders, suborders = ExecutedOfThePeriodData(self.start_period, self.end_period).get_data()
        self.ws["A1"] = f"Внутренние распорядительные документы со сроками исполнения в период с {self.srp} по {self.erp}"
        self.ws['A2'] = None
        
        self.ws.append(REPORT_HEADER)
        #Это пиздец, переделать
        _idx = 0
        for row_idx, order in enumerate(orders, 4):
            if _idx != 0:
                row_idx = _idx + 1
            self.ws[f'A{row_idx}'] = order.issue_type
            self.ws[f'B{row_idx}'] = order.issue_idx
            self.ws[f'C{row_idx}'] = order.approving_date
            self.ws[f'D{row_idx}'] = order.title
            self.ws[f'E{row_idx}'] = order.initiator
            self.ws[f'F{row_idx}'] = order.approving_employee
            self.ws[f'G{row_idx}'] = order.employee
            self.ws[f'H{row_idx}'] = order.deadline
            self.ws[f'J{row_idx}'] = order.status_code
            self.ws[f'K{row_idx}'] = order.comment
            for subrow_idx, suborder in enumerate(suborders, row_idx+1):
                self._fill_row(subrow_idx, suborder)
                self.ws[f'A{subrow_idx}'] = 'Поручение'
                self.ws[f'B{subrow_idx}'] = order.issue_idx
                self.ws[f'G{subrow_idx}'] = suborder.employee
                self.ws[f'H{subrow_idx}'] = suborder.deadline
                self.ws[f'I{subrow_idx}'] = suborder.content
                self.ws[f'J{subrow_idx}'] = suborder.status_code
                self.ws[f'K{subrow_idx}'] = suborder.comment
                _idx = subrow_idx
                print(f'{subrow_idx=}')

    def _apply_styles(self) -> None:
        self._data_to_sheet()
        self.ws.merge_cells('A1:K1')
        self.ws['A1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.ws['A1'].font = Font(name='Times New Roman', size=12, bold=True)
        self.ws.auto_filter.ref = "A3:K3"
        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        #HEADER
        for cell in self.ws['3:3']:
            cell.fill = PatternFill(fill_type='solid', fgColor="DBE5F1")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.font = Font(name='Times New Roman', size=12, bold=True)
            cell.border = border

        for row in self.ws.iter_rows(min_row=4):
            for col_idx, cell in enumerate(row, 1):
                self.ws.column_dimensions[get_column_letter(col_idx)].width = REPORT_HEADER_WIDTH[col_idx - 1] 
                cell.font = Font(name='Times New Roman', size=12, bold=False)
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                cell.border = border

    def form(self) -> bytes:
        self._apply_styles()
        self.wb.save("ExecutedVRD.xlsx")
        return self.wb


class ApprovedPeriodData:
    """
    Осуществляет выборку утвержденных ВРД за период из БД
    """
    orders_table = Table('orders')
    suborders_table = Table("suborders")

    def __init__(self, start_period: datetime, end_period: datetime) -> None:
        self.start_report_period = start_period
        self.end_report_period = end_period

    def _get_orders(self) -> list[ReportOrderRow]:
        q = Query.from_(self.orders_table).select(
                self.orders_table.id,
                self.orders_table.issue_type,
                self.orders_table.issue_idx,
                self.orders_table.approving_date,
                self.orders_table.title,
                self.orders_table.initiator,
                self.orders_table.approving_employee,
                self.orders_table.employee,
                self.orders_table.deadline,
                self.orders_table.status_code,
                self.orders_table.comment
        ).where(
            self.orders_table.approving_date[self.start_report_period:self.end_report_period]
        )
        orders = rawrows_to_reportrows(ORDERS_HEADER, OrdersTable().execute_query(str(q)), ReportOrderRow)
        return orders

    def get_data(self) -> tuple[Any]:
        orders = self._get_orders()
        orders_ids = [row.id for row in orders]
        q = Query.from_(self.suborders_table).select(
                self.suborders_table.id_orders,
                self.suborders_table.content,
                self.suborders_table.deadline,
                self.suborders_table.status_code,
                self.suborders_table.employee,
                self.suborders_table.comment,
                self.suborders_table.close_date,
        ).where(
            (self.suborders_table.id_orders.isin(orders_ids)) &
            (self.suborders_table.deleted == False)
        )
        suborders = rawrows_to_reportrows(SUBORDERS_HEADER, SubOrdersTable().execute_query(str(q)), ReportSuborderRow)
        return orders, suborders


class ApprovedForThePeriod:
    """
    Отчет об утвержденных за период ВРД
    """

    def __init__(self, start_period: datetime, end_period: datetime, wb: Workbook) -> None:
        self.output = BytesIO()
        self.start_period = start_period
        self.end_period = end_period
        self.srp = datetime.strptime(start_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.erp = datetime.strptime(end_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.wb = wb
        self.ws = self.wb.active
        self.ws.title = "Утвержденные за период"

    def _fill_row(self, row_idx: int, row: Any) -> None:
        if row.status_code == "На исполнении":
            _fill = PatternFill(fill_type='solid', fgColor="E6B9B8")
        elif row.status_code == "Заершено":
            _fill = PatternFill(fill_type='solid', fgColor="8DB4E3")
        elif row.deadline == datetime.now().date().replace(month=12, day=31).strftime("%d.%m.%Y"):
            _fill = PatternFill(fill_type='solid', fgColor="D7E4BC")
        else:
            _fill = PatternFill(fill_type='solid', fgColor="FFFFFF")
        for col_idx in range(1, self.ws.max_column + 1):
            self.ws.cell(row_idx, col_idx).fill = _fill

    def _data_to_sheet(self):
        self.ws["A1"] = f"Внутренние распорядительные документы, утвержденные в период с {self.srp} по {self.erp}"
        self.ws["B2"] = '- без установленных сроков'
        self.ws["B3"] = '- на исполнении'
        self.ws["B4"] = '- завершено'
        self.ws['B5'] = None
        self.ws.append(REPORT_HEADER)
        orders, suborders = ApprovedPeriodData(self.start_period, self.end_period).get_data()
        _idx = 0
        for row_idx, order in enumerate(orders, 7):
            if _idx != 0:
                row_idx = _idx + 1
            self._fill_row(row_idx, order)
            self.ws[f'A{row_idx}'] = order.issue_type
            self.ws[f'B{row_idx}'] = order.issue_idx
            self.ws[f'C{row_idx}'] = order.approving_date
            self.ws[f'D{row_idx}'] = order.title
            self.ws[f'E{row_idx}'] = order.initiator
            self.ws[f'F{row_idx}'] = order.approving_employee
            self.ws[f'G{row_idx}'] = order.employee
            self.ws[f'H{row_idx}'] = order.deadline
            self.ws[f'J{row_idx}'] = order.status_code
            self.ws[f'K{row_idx}'] = order.comment

            for subrow_idx, suborder in enumerate(suborders, row_idx + 1):
                self._fill_row(subrow_idx, suborder)
                self.ws[f'A{subrow_idx}'] = 'Поручение'
                self.ws[f'B{subrow_idx}'] = order.issue_idx
                self.ws[f'G{subrow_idx}'] = suborder.employee
                self.ws[f'H{subrow_idx}'] = suborder.deadline
                self.ws[f'I{subrow_idx}'] = suborder.content
                self.ws[f'J{subrow_idx}'] = suborder.status_code
                self.ws[f'K{subrow_idx}'] = suborder.comment
                _idx = subrow_idx

    def _apply_styles(self):
        self.ws.merge_cells('A1:K1')
        self.ws['A1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.ws['A1'].font = Font(name='Times New Roman', size=12, bold=True)
        self.ws.auto_filter.ref = "A6:K6"
        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        
        #Ячейки с расшифровкой заливки
        for cell in ('A2', 'A3', 'A4'):
            self.ws[cell].border = border
        self.ws['A2'].fill = PatternFill(fill_type='solid', fgColor="D7E4BC")
        self.ws['A3'].fill = PatternFill(fill_type='solid', fgColor="E6B9B8")
        self.ws['A4'].fill = PatternFill(fill_type='solid', fgColor="8DB4E3")

        #HEADER
        for cell in self.ws['6:6']:
            cell.fill = PatternFill(fill_type='solid', fgColor="DBE5F1")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.font = Font(name='Times New Roman', size=12, bold=True)
            cell.border = border
            
        for row in self.ws.iter_rows(min_row=7):
            for col_idx, cell in enumerate(row, 1):
                self.ws.column_dimensions[get_column_letter(col_idx)].width = REPORT_HEADER_WIDTH[col_idx - 1] 
                cell.font = Font(name='Times New Roman', size=12, bold=False)
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                cell.border = border

    def form(self) -> bytes:
        self._data_to_sheet()
        self._apply_styles()
        return self.wb

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
        self.end_report_period = "2022-11-10"
        self.srp = datetime.strptime(self.start_report_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.erp = datetime.strptime(self.end_report_period, "%Y-%m-%d").strftime("%d.%m.%Y")
        self.output = BytesIO()
        self.wb = Workbook()

    def form_approved_for_the_period(self) -> None:
        approved_period = ApprovedForThePeriod(
            self.start_report_period,
            self.end_report_period,
            self.wb).form()
        self.wb = approved_period

    def form_executed_for_the_period(self) -> bytes:
        wb = ExecutedOfThePeriod(
            self.start_report_period,
            self.end_report_period,
            self.wb
        ).form()
        wb.save(self.output)
        return self.output.getvalue() 

    def send_report(self) -> None:
        self.form_approved_for_the_period()
        Email.send_weekly_report(
            f"""Отчет об исполнении за период {self.srp} - {self.erp}\n\n"""
            """*Данное сообщение сформированно автоматическе. Не нжуно на него отвечать.\n\n""",
            f"weekly_report {self.srp}-{self.erp}",
            self.form_executed_for_the_period()
        )

WeeklyReport().send_report()