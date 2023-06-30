from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from reminder_schedule import Reminder
from reports import WeeklyReport
import logging
from logger.logger import *


logger = logging.getLogger(__name__)


async def remind_to_employ(scheduler: AsyncIOScheduler) -> None:
    """
    Планировщик напоминаний об исполнении поручений 
    """
    try:
        trigger = OrTrigger([
            CronTrigger(day_of_week=day, hour=6, minute=30)
                for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
        ])

        scheduler.add_job(
            Reminder().remind_to_employee,
            trigger=trigger,
            id="reminder",
            replace_existing=True,
        )
    except Exception as e:
        logger.error(f"Ошибка планировщика: {e}")

def send_weekly_report(scheduler: AsyncIOScheduler) -> None:
    """
    Планировщик рассылки отчетов
    """
    try:
        trigger = CronTrigger(day_of_week='fri', hour=7, minute=30)
        scheduler.add_job(
            WeeklyReport().send_report,
            trigger=trigger,
            id="weekly_report",
            replace_existing=True,
        )
    except Exception as e:
        logger.error(f"Ошибка отчета: {e}")
