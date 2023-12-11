from fastapi import APIRouter, Depends, Response
import logging
from logger.logger import *
from database.data import *
from reports import manual_report_unloading, WeeklyReport


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/report", tags=['report'])


@router.get("/weekly", status_code=200)
async def send_weekly():
    wr = WeeklyReport()
    wr.send_report()


@router.get("/by_period")
async def report_by_period(period = Depends(Period)):
    try:
        data = manual_report_unloading(period)
        headers = {
                'content-disposition':
                f'attachment; filename="manual_report({period.start_period}-{period.end_period}).xlsx"'
        }
        logger.info(f'Ручная выгрузка отчета за период {period.start_period}-{period.end_period}')
        return Response(content=data, headers=headers)
    except Exception as e:
        logger.error(f'Ошибка при ручной выгрузке отчета -> {e}')