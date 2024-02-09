import cx_Oracle_async
from database.utils import query_from_file
import os
from dotenv import load_dotenv

load_dotenv()


IBS_HOST=os.getenv("IBS_HOST")
IBS_PORT=os.getenv("IBS_PORT")
IBS_SERVICE_NAME=os.getenv("IBS_SERVICE_NAME")
IBS_USER=os.getenv("IBS_USER")
IBS_PWD=os.getenv("IBS_PWD")


async def _oracle_pool():
    return await cx_Oracle_async.create_pool(
                host=IBS_HOST, 
                port=IBS_PORT,
                user=IBS_USER, 
                password=IBS_PWD,
                service_name=IBS_SERVICE_NAME, 
                min = 2,
                max = 30,
    )


async def get_users_and_emails():
    """
    Список пользователей и их почты
    """
    pool = await _oracle_pool()
    async with pool.acquire() as connection:
       async with connection.cursor() as cursor:
           query = query_from_file('database/sql/ibso_employees.sql') 
           await cursor.execute(query)
           data = await cursor.fetchall()
    await pool.close()
    return [{"email": email, "user_name": name} for email, name in data]