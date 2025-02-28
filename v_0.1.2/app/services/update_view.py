from typing import List
from pydantic import BaseModel
from sqlite_database import update_order
from utils import log_decorator

class CancelUpdate(BaseModel):
    updates: List[dict]  # 各辞書は {"order_id": int, "canceled": bool} の形式

@app.post("/update_cancel_status")
@log_decorator
async def update_cancel_status(update: CancelUpdate):
    results = []
    for change in update.updates:
        order_id = change["order_id"]
        canceled = change["canceled"]
        print(f"更新 order_id: {order_id}, canceled: {canceled}")
        
        # ここに SQL の UPDATE 文を実行するコードを入れる
        # 例: await database.execute("UPDATE orders SET canceled = $1 WHERE order_id = $2", canceled, order_id)
        await update_order(order_id, canceled)
        results.append({"order_id": order_id, "canceled": canceled, "success": True})
    
    return {"results": results}