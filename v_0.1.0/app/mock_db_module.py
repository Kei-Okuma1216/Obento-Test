from datetime import datetime, timedelta
from functools import wraps
import logging
import sqlite3
from typing import Optional

# ログ用の設定
logging.basicConfig(level=logging.INFO)

# カスタムデコレーターを定義
def log_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging.info("- %s 前", func.__name__)
        result = await func(*args, **kwargs)
        logging.info("- %s 後", func.__name__)
        return result
    return wrapper

# データベース初期化
# インメモリデータベースを作成
#conn = sqlite3.connect(':memory:')
db_name_str = "example.db"

def get_connection(): 
     conn = sqlite3.connect('example.db') 
     #conn = sqlite3.connect({{db_name_str}}) 
     
     # データベースファイル名を指定 
     return conn

def get_database():
    return

def delete_database():
    reset_orders_autoincrement()
    delete_all_orders()
    delete_all_user()
    return

def init_database():
    print("init_database()開始")
    try:
          conn = get_connection()
          if conn is None: 
               print("データベース接続の確立に失敗しました。")
          
          #reset_orders_autoincrement()
          #delete_all_orders()
          #delete_all_user()
          
          cursor = conn.cursor()
          print("create_user_table()")
          create_user_table(cursor) 
          insert_user("user1", "user1", "大隈 慶1", '', '', 1)
          insert_user("user2", "user2", "大隈 慶2", '', '', 1)
          insert_user("shop", "shop", "お店", '', '', 2)
          create_orders_table(cursor)
          insert_order(1, 1, 1, "user1",1)
          insert_order(1, 1, 1, "user2", 2)
          insert_order(1, 1, 1,"tenten01", 3)
          #print("show_all_orders()直前")
          #show_all_orders()
          #print("show_all_orders()直後")

          conn.close() 
          print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"Error: {str(e)}")
        import traceback 
        traceback.print_exc()

# Ordersテーブルを作成
def create_orders_table(cursor):
     print("create_orders_table()")
     cursor.execute('''
     CREATE TABLE IF NOT EXISTS Orders (
     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
     shop_id INTEGER,
     menu_id INTEGER,
     company_id INTEGER,
     user_id TEXT,
     amount INTEGER,
     order_date TEXT
     canceled BOOLEAN DEFAULT FALSE
     )
     ''')

# AUTOINCREMENTフィールドをリセット
def reset_orders_autoincrement():
    try:    
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Orders"')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
    return

def delete_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS Orders')
    #cursor.execute('DELETE FROM Orders')    
    conn.commit()
    conn.close()

def delete_all_user():
    try:
        reset_orders_autoincrement()
        
        conn = get_connection()
        cursor = conn.cursor()
        #cursor.execute('DELETE FROM User')    
        cursor.execute('DROP TABLE IF EXISTS User')
        conn.commit()
        conn.close()
    except Exception as e:    
        print(f"Error: {e}")
    finally:
        conn.close()

# コネクションを閉じる（実際のテストでは不要）
#conn.close()



def get_today_str(add_days: int = 0):
    # 例: 2025-01-23 10:34
    #return datetime.now().strftime("%Y-%m-%d %H:%M")
    new_date = datetime.now() - timedelta(days=add_days)
    return new_date.strftime("%Y-%m-%d %H:%M")

    #return datetime.now() - timedelta(days=add_days).strftime("%Y-%m-%d %H:%M")

def get_yesterday_str():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d %H:%M")

# テスト用のOrderテーブルに偽注文を追加する
# Ordersテーブルを作成
def create_orders_table(cursor):
     cursor.execute('''
     CREATE TABLE Orders (
     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
     shop_id INTEGER,
     menu_id INTEGER,
     company_id INTEGER,
     user_id TEXT,
     amount INTEGER,
     order_date TEXT,
     canceled BOOLEAN DEFAULT FALSE
     )
     ''')
     
@log_decorator
def insert_order(shop_id, menu_id, company_id, user_id, amount):
    print("INSERT Orders 前")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Orders (shop_id, menu_id, company_id, user_id, amount, order_date)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (shop_id, menu_id, company_id, user_id, amount, get_today_str(-1)))
    conn.commit()
    conn.close()

# 今日の注文を検索する
@log_decorator
def select_today_orders(shopid: int)-> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("SELECT Orders 前")           
        cursor.execute(
            'SELECT * FROM Orders WHERE user_id = ? AND date(order_date) = date("now", "-1 day")',
            (shopid,))
        rows = cursor.fetchall()  # または fetchall() を使用
        print("rows: " + str(rows))
        print("SELECT Orders 後")
        if rows is None:
            raise ValueError("No order found with the given shopid")
        
        # 辞書型のリストとして結果を返却
        orders = {}
        for row in rows:
            orders.append({
                "order_id": row[0],
                "company_id": row[1],
                "user_id": row[2],
                "menu_id": row[3],
                "amount": row[4],
                "order_date": row[5],
                "canceled": row[6]
            })
        # リストをJSON形式に変換して返す
        return orders#json.dumps(orders, ensure_ascii=False)
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

# Orderデータの確認
@log_decorator
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
     name TEXT,
     token TEXT DEFAULT NULL,
     expire_date TEXT DEFAULT NULL,
     permission INTEGER DEFAULT 1
     )
     ''')

# テスト用の偽ユーザーを追加する
@log_decorator
def insert_user(user_id, password, name, token, expire_date, permission):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("INSERT User 前")
        
        # user_idの存在を確認
        cursor.execute('SELECT COUNT(*) FROM User WHERE user_id = ?', (user_id,))
        if cursor.fetchone()[0] > 0:
            print(f"ユーザーID {user_id} は既に存在します。挿入をスキップします。")
        else:
            print('INSERT INTO 直前')
            cursor.execute('''
            INSERT INTO User (user_id, password, name, token, expire_date, permission)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, password, name, '', '', permission))
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()
    
# ユーザーを検索する
@log_decorator
def select_user(user_id: str)-> Optional[dict]:
    print("select_user()")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()  # または fetchall() を使用
        
        print(row)

        if row is None:
            raise ValueError(
                "No user found with the given user_id")
        # 結果を辞書形式に変換        
        result = {
                "user_id": row[0],
                "password": row[1],
                "name": row[2],
                "token": row[3],
                "expire_date" : row[4],
                "permission": row[5]
            }
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

    return result

# Userデータの確認
@log_decorator
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

# tokenの更新
@log_decorator
def update_user(user_id, token):
    print("update_user()前")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE User SET token = ? WHERE user_id = ?
        ''', (token, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        print("update_user()エラーあり")
    finally:
        conn.close()
        print("update_user()後")
    return

