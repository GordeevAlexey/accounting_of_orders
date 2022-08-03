import json
from database.db import DBConnection



def get_orders() -> json:
    headers = (
        'id',
        'title',
        'creator',
        'initiator',
        'employee',
        'department',
        'create_date',
        'deadline date',
        'close_date',
        'status_code',
        'text_close',
    )
    orders = DBConnection.get_orders()
    result = []
    for row in orders:
        result.append({k: v for k,v in zip(headers, row)})
    return json.dumps(result)