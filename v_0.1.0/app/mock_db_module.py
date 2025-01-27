from datetime import datetime, timedelta
from functools import wraps
import logging
from pprint import pprint
from typing import Optional
import sqlite3
import warnings

# ログ用の設定
logging.basicConfig(level=logging.INFO)

# カスタムデコレーターを定義
def log_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("- %s 前", func.__name__)
        result = func(*args, **kwargs)
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

# Userテーブルを作成する
@log_decorator
def create_user_table():
    try:
        conn = get_connection()
        if conn is None: 
            print("データベース接続の確立に失敗しました。")        
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
        user_id TEXT PRIMARY KEY,
        password TEXT,
        name TEXT,
        token TEXT DEFAULT NULL,
        expire_date TEXT DEFAULT NULL,
        shop_id TEXT DEFAULT NULL,
        menu_id INTEGER NULL,
        permission INTEGER DEFAULT 1
        )
        ''')
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
    finally:
        conn.close()

# Ordersテーブルを作成
@log_decorator
def create_orders_table():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
        '''CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        user_id TEXT,
        shop_id INTEGER,
        menu_id INTEGER,
        amount INTEGER,
        order_date TEXT,
        canceled BOOLEAN DEFAULT FALSE
        )''')
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
    finally:
        conn.close()


# コネクションを閉じる（実際のテストでは不要）
#conn.close()


@log_decorator
def get_today_str(add_days: int = 0):
    # 例: 2025-01-23 10:34
    #return datetime.now().strftime("%Y-%m-%d %H:%M")
    new_date = datetime.now() - timedelta(days=add_days)
    return new_date.strftime("%Y-%m-%d %H:%M")

    #return datetime.now() - timedelta(days=add_days).strftime("%Y-%m-%d %H:%M")
@log_decorator
def get_yesterday_str():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d %H:%M")

# テスト用のOrderテーブルに偽注文を追加する
# Ordersテーブルを作成
@log_decorator
def create_orders_table():
    try:
        conn = get_connection() 
        if conn is None: 
            print("データベース接続の確立に失敗しました。")        
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        user_id TEXT,
        shop_id INTEGER,
        menu_id INTEGER,
        amount INTEGER,
        order_date TEXT,
        canceled BOOLEAN DEFAULT FALSE
        )
        ''')
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
    finally:
        conn.close()

# 今日の注文を検索する
@log_decorator
def select_today_orders(shopid: int)-> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM Orders WHERE user_id = ? AND date(order_date) = date("now", "-1 day")',
            (shopid,))
        rows = cursor.fetchall()  # または fetchall() を使用
        print("rows: " + str(rows))
        if rows is None:
            warnings.warn("No order found with the given shopid")
        
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
        pprint(orders)
        return orders#json.dumps(orders, ensure_ascii=False)
    except Exception as e:
        pprint(f"Error: {e}")
        return None
    finally:
        conn.close()

# Orderデータの確認
@log_decorator
def show_all_orders():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Orders')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()

@log_decorator
def insert_order(company_id, user_id, shop_id, menu_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Orders (company_id, user_id, shop_id, menu_id,  amount, order_date)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (company_id, user_id, shop_id, menu_id,  amount, get_today_str(-1)))
    conn.commit()
    conn.close()

# tokenの更新
@log_decorator
def update_user(user_id, key, value):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("key:" + key)
        print("value:" + value)
        cursor.execute('''
        UPDATE User SET key = ? WHERE user_id = ?
        ''', (key, value, user_id))
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
    finally:
        conn.close()
    return



# テスト用の偽shopユーザーを作成する
@log_decorator
def insert_shop(user_id, password, name):
    try:
        # 備考：user_id == shop_id とする
        conn = get_connection()
        cursor = conn.cursor()
        # user_idの存在を確認
        cursor.execute('SELECT COUNT(*) FROM User WHERE user_id = ?', (user_id,))
        if cursor.fetchone()[0] > 0:
            print(f"このユーザーID {user_id} は既に存在します。挿入をスキップします。")
        else:
            print('INSERT INTO 直前')
            cursor.execute('''
            INSERT INTO User (
                user_id, password, name, token, expire_date, shop_id, menu_id, permission)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, password, name, '', '9999-12-31 23:59', user_id, 1, 2))
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
        return None
    finally:
        conn.close()


# テスト用の偽ユーザーを追加する
@log_decorator
def insert_user(user_id, password, name, shop_id, menu_id, permission):
    try:
        conn = get_connection()
        cursor = conn.cursor()       
        # user_idの存在を確認
        cursor.execute('SELECT COUNT(*) FROM User WHERE user_id = ?', (user_id,))
        if cursor.fetchone()[0] > 0:
            print(f"ユーザーID {user_id} は既に存在します。挿入をスキップします。")
        else:
            print('INSERT INTO 直前')
            cursor.execute('''
            INSERT INTO User (user_id, password, name, token, expire_date, shop_id, menu_id, permission)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, password, name, '', '', shop_id, menu_id, permission))
        conn.commit()
    except Exception as e:
        pprint(f"Error: {e}")
        return None
    finally:
        conn.close()
    
# ユーザーを検索する
@log_decorator
def select_user(user_id: str)-> Optional[dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()  # または fetchall() を使用
        
        print(row) # いなければNone

        if row is None:
            warnings.warn(
                "No user found with the given user_id")
        # 結果を辞書形式に変換        
        result = {
                "user_id": row[0],
                "password": row[1],
                "name": row[2],
                "token": row[3],
                "expire_date" : row[4],
                "shop_id" : row[5],
                "menu_id" : row[6],
                "permission": row[7]
            }
            
    except Exception as e:
        pprint(f"Error: {e}")
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




def delete_database():
    reset_orders_autoincrement()
    delete_all_orders()
    delete_all_user()
    return

# AUTOINCREMENTフィールドをリセット
@log_decorator
def reset_orders_autoincrement():
    try:    
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Orders"')
        
        conn.commit()
        conn.close()
    except Exception as e:
        pprint(f"Error: {e}")
    return

@log_decorator
def delete_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS Orders')
    #cursor.execute('DELETE FROM Orders')    
    conn.commit()
    conn.close()

@log_decorator
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
        pprint(f"Error: {e}")
    finally:
        conn.close()

@log_decorator
def init_database():
    try:
          create_user_table() 
          insert_user("user1", "user1", "大隈 慶1", "shop01", 1, 1)
          insert_user("user2", "user2", "大隈 慶2", "shop01", 1, 1)
          insert_shop("shop01", "shop01", "お店shop01")
          
          create_orders_table()
          '''INSERT INTO Orders (company_id, user_id, shop_id, menu_id,  amount, order_date)
          VALUES (?, ?, ?, ?, ?, ?)'''
          insert_order(1, "user1", "shop01", 1, 1)
          insert_order(1, "user2", "shop01", 1, 2)
          insert_order(1, "tenten01", "shop01", 1, 3)
          show_all_orders()

          print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"Error: {str(e)}")
        import traceback 
        traceback.print_exc()
