from fastapi import APIRouter, Depends, HTTPException
import logging
from logger.logger import *
from database.data import *



logger = logging.getLogger(__name__)


router = APIRouter(prefix="/order", tags=['order'])

@router.patch("/update")
async def update_order(order=Depends(Order)):
    o = order.dict()
    employees_to_string(o)
    OrdersTable().update_order(o)
    return RedirectResponse("/", status_code=303)


@roiter.delete("/delete")
async def delete_order(id: str):
    OrdersTable().delete_order_row(id)
    return RedirectResponse("/", status_code=303)


@router.post("/add_order")
@app.post("/add_order")
async def add_order(order = Depends(NewOrder)):
    o = order.dict()
    employees_to_string(o)
    OrdersTable().add_order(o)
    return RedirectResponse("/", status_code=303)


@router.get("/orders_bar")
async def get_order():
    return OrdersTable().get_orders_table_pg_bar()