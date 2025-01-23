from datetime import date 
import sqlite3
from typing import Optional

# データベース初期化
# インメモリデータベースを作成
#conn = sqlite3.connect(':memory:')
db_name_str = "example.db"

def get_connection(): 
     conn = sqlite3.connect('example.db') 
     #conn = sqlite3.connect({{db_name_str}}) 
     
     # データベースファイル名を指定 
     return conn

def init_database():
    print("init_database()開始")
    try:
          conn = get_connection()
          if conn is None: 
               print("データベース接続の確立に失敗しました。")
          cursor = conn.cursor()
          #create_user_table(cursor) 
          #insert_user(conn, "k.okuma", "aaa", 1)
          #insert_user(conn, "k.okuma@ten-system.com", "aaa12345", 3)
          #create_order_table(cursor)
          insert_order(1, "k.okuma@ten-system.com",1, 1)
          insert_order(1, "okuma112", 1, 1)
          insert_order(1, "tenten01", 1, 1)
          #print("show_all_orders()直前")
          #show_all_orders()
          #print("show_all_orders()直後")
          
          #reset_autoincrement()
          conn.close() 
          print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"Error: {str(e)}")
        import traceback 
        traceback.print_exc()

# Orderテーブルを作成
def create_order_table(cursor):
     cursor.execute('''
     CREATE TABLE IF NOT EXISTS Orders (
     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
     company_id INTEGER,
     name TEXT,
     menu INTEGER,
     amount INTEGER,
     order_date TEXT
     canceled BOOLEAN DEFAULT FALSE
     )
     ''')

# AUTOINCREMENTフィールドをリセット
def reset_autoincrement():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Orders"')
    
    conn.commit()
    conn.close()
    
# コネクションを閉じる（実際のテストでは不要）
#conn.close()


# order_id番号増加
number = 0
def increment_id():
    return number + 1
# 例: 2025-01-23 10:34
def get_today_str():
    return date.today().strftime("%Y-%m-%d %H:%M")

# テスト用のOrderテーブルに偽注文を追加する
def insert_order(company_id, name, menu, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Orders (order_id, company_id, name, menu, amount, order_date)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (increment_id(), company_id, name, menu, amount, get_today_str()))
    conn.commit()
    conn.close()

# 今日の注文を検索する
async def select_today_orders(shopid: str)-> Optional[dict]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            print("SELECT Orders 前")           
            cursor.execute(
                'SELECT * FROM Orders WHERE user_id = ? AND date(order_date) = date("now", "-1 day")',
                (shopid,))
            rows = cursor.fetchall()  # または fetchall() を使用
            print("SELECT Orders 後")
            if rows is None:
                    raise ValueError("No order found with the given shopid")
            # 辞書型のリストとして結果を返却
            orders = []
            for row in rows:
                '''{'order_id': 1, 'company_id': 1,
                'name':"大隈 慶1", "menu": 1, "amount": 1, "order_date": "2025-1-22 10:54"},'''
                orders.append({
                    "order_id": row[0],
                    "company_id": row[1],
                    "name": row[2],
                    "menu": row[3],
                    "amount": row[4],
                    "order_date": row[5],
                    "canceled": row[6]
                })
            return orders
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            conn.close()

# Orderデータの確認
def show_all_orders():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print('手前 SELECT * FROM Orders')
        cursor.execute('SELECT * FROM Orders')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()
        
# テスト用のUserテーブルを作成する
def create_user_table(cursor):
     cursor.execute('''
     CREATE TABLE IF NOT EXISTS User (
     user_id TEXT PRIMARY KEY,
     password TEXT,
     token TEXT,
     permission INTEGER DEFAULT 1
     )
     ''')

# テスト用の偽ユーザーを追加する
def insert_user(conn, user_id, password, permission):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO User (user_id, password, permission)
    VALUES (?, ?, ?)
    ''', (user_id, password, permission))
    conn.commit()
    conn.close()
    
# ユーザーを検索する
async def select_user(user_id: int)-> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        print("SELECT User 前")
        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()  # または fetchall() を使用
        print("SELECT User 後")
        if row is None:
                raise ValueError(
                    "No user found with the given user_id")
        # 結果を辞書形式に変換        
        #print("row[0]: " + row[0])
        if row:
            result = {
                "user_id": row[0],
                "password": row[1],
                "token": row[2],
                "permission": row[3],
            }
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

    return result

# Userデータの確認
def show_all_users():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()