import json
import logging
from pprint import pprint
from typing import List, Optional
import sqlite3
import warnings
from utils import deprecated, log_decorator, get_today_str 
#from models import Order, User
from schemas import Order, User
#from .schemas.schemas import Order, User
import aiosqlite

# ログ用の設定
logging.basicConfig(level=logging.INFO)

default_shop_name = "shop01"

# データベース初期化
# インメモリデータベースを作成
#conn = sqlite3.connect(':memory:')
db_name_str = "example.db"

# コネクション取得
async def get_connection(): 
    # return await sqlite3.connect('example.db') 
    return await aiosqlite.connect('example.db')
     #conn = sqlite3.connect({{db_name_str}}) 
     

# コネクションを閉じる（実際のテストでは不要）
#await conn.close()



# Userテーブル
# 作成
#@log_decorator
async def create_user_table():
    try:
        conn = await get_connection()
        if conn is None: 
            print("データベース接続の確立に失敗しました。")
            return        
        #cursor = conn.cursor()
        #await cursor.execute('''

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS User (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        name TEXT DEFAULT NULL,
        token TEXT DEFAULT NULL,
        exp TEXT DEFAULT NULL,
        company_id int DEFAULT NULL,
        shop_name TEXT DEFAULT NULL,
        menu_id int NULL,
        permission INTEGER DEFAULT 1,
        is_modified INTEGER DEFAULT 0,
        updated_at TEXT
        )
        ''')
        await conn.commit()
    except Exception as e:
        print(f"create_user_table Error: {e}")
    finally:
        if conn:
            await conn.close()

# ユーザー
# 検索
@log_decorator
async def select_user(username: str)-> Optional[User]:
    try:
        #print(f"username: {username}")
        conn = await get_connection()
        
        async with conn.cursor() as cursor:
            sanitized_username = username.strip()
            sqlStr = "SELECT * FROM User WHERE username = ?"
            await cursor.execute(sqlStr, (sanitized_username,))
            row = await cursor.fetchone()

        if row is None:
            #warnings.warn(
            print(
                "No user found with the given username")
            return None  # ユーザーが存在しない場合
        user = User(
            user_id=row[0],
            username=row[1],            
            password=row[2],
            name=row[3],
            token=row[4],
            exp=row[5],
            company_id=row[6],
            shop_name=row[7],
            menu_id=row[8],
            permission=row[9],
            is_modified=row[10],
            updated_at=row[11]
        )
        return user
    except Exception as e:
        print(f"select_user Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()

# 新規ユーザーの登録
@log_decorator
async def insert_new_user(username, password, name = ''):
    try:
        await insert_user(username, password, name, company_id=1, shop_name=default_shop_name, menu_id=1)
    except Exception as e:
        print(f"insert_new_user Error: {e}")

# 追加
@log_decorator
async def insert_user(username, password, name, company_id, shop_name, menu_id):
    try:
        conn = await get_connection()
        #cursor = conn.cursor()       
        # usernameの存在を確認
         # usernameの存在を確認（fetchone() を直接取得）
        result = await conn.execute('SELECT COUNT(*) FROM User WHERE username = ?', (username,))
        count = (await result.fetchone())[0]  # カーソルを明示的に使わず取得
        
        if count > 0:
            print(f"ユーザーID: {username} は既に存在します。挿入をスキップします。")
            return False  # 既に存在する場合は False を返す
        else:
            #print('INSERT INTO 直前')
            await conn.execute('''
            INSERT INTO User (username, password, name, token, exp, company_id, shop_name, menu_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, name, '', '', company_id, shop_name, menu_id))

            await conn.commit()  # INSERT が実行されたときのみ commit()
            print(f"ユーザー {username} を追加しました。")
            return True  # 挿入成功時は True を返す

    except Exception as e:
        print(f"insert_user Error: {e}")
        return None  # エラー時は None を返す
    finally:
        if conn:
            await conn.close()

# お弁当屋追加
@log_decorator
async def insert_shop(username, password, shop_name):
    try:
        # 備考：username == shop_name とする
        conn = await get_connection()
        result = await conn.execute('SELECT COUNT(*) FROM User WHERE username = ?', (username,))
        count = (await result.fetchone())[0]  # カーソルを明示的に使わず取得
        # usernameの存在を確認
        #await cursor.execute('SELECT COUNT(*) FROM User WHERE username = ?', (username,))
        if count > 0:
            print(f"このユーザーID {username} は既に存在します。挿入をスキップします。")
        else:
            #print('INSERT INTO 直前')
            await conn.execute('''
            INSERT INTO User (
                username, password, name, token, exp, company_id, shop_name, menu_id, permission)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, shop_name, '', '9999-12-31 23:59', 1, username, 1, 2))
        await conn.commit()
    except Exception as e:
        print(f"insert_shop Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()



# 更新
#@log_decorator
async def update_user(username, key, value):
    try:
        conn = await get_connection()
        async with conn.cursor() as cursor:
            query = f"UPDATE User SET {key} = ? WHERE username = ?"
            await cursor.execute(query, (value, username))
            await conn.commit()  # 非同期の `commit()`
    except Exception as e:
        print(f"update_user Error: {e}")
    finally:
        if conn:
            await conn.close()
    return

# 全件確認
@log_decorator
async def show_all_users():
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        await cursor.execute('SELECT * FROM User')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    finally:
        if conn:
            await conn.close()

# Companyお客様団体テーブル
# 作成
#@log_decorator
async def create_company_table():
    conn = None
    try:
        conn = await get_connection()
        if conn is None: 
            print("データベース接続の確立に失敗しました。")
            return        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS Company (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tel TEXT DEFAULT NULL,
            shop_name TEXT DEFAULT NULL,
            created_at TEXT,
            disabled INTEGER DEFAULT 0
        )
        ''')
        await conn.commit()
        print("companyテーブルができました")
    except Exception as e:
        print(f"create_company_table Error: {e}")
    finally:
        if conn:
            await conn.close()

# 追加
@log_decorator
async def insert_company(name, tel, shop_name):
    conn = None
    try:
        conn = await get_connection()
        #cursor = conn.cursor()
        # SQL文を文字列として定義
        sql_query = '''
        INSERT INTO Company (name, tel, shop_name, created_at, disabled)
        VALUES (?, ?, ?, ?, ?)
        '''
        values = (name, tel, shop_name, get_today_str(), False)

        #print(f"SQL Query: {sql_query}")
        #print(f"Values: {values}")
        # SQL文と値をcursor.executeに渡して実行
        await conn.execute(sql_query, values)
        await conn.commit()
    except Exception as e:
        print(f"insert_company Error: {e}")  # エラーメッセージを表示
    finally:
        if conn:
            await conn.close()


# 注文テーブル
# 作成
#@log_decorator
async def create_orders_table():
    conn = None
    try:
        conn = await get_connection() 
        if conn is None: 
            print("データベース接続の確立に失敗しました。")
            return
        await conn.execute('''
            CREATE TABLE Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            username TEXT,
            shop_name TEXT,
            menu_id INTEGER,
            amount INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            canceled INTEGER DEFAULT 0
            )
        ''')
        await conn.commit()
    except Exception as e:
        print(f"create_orders_table Error: {e}")
    finally:
        if conn:
            await conn.close()

# 選択
@deprecated
@log_decorator
async def select_all_orders2(shop_name: str = None, days_ago_str: str = 0)-> Optional[List[Order]]:
    conn = None
    try:
        days_ago = int(days_ago_str)
        if  days_ago > 0:
            #arise format_exception
            days_ago = 0
            
        conn = await get_connection()
        cursor = await conn.cursor()

        sqlstr = f"SELECT * FROM Orders"
        if shop_name is None and days_ago is None:
            sqlstr += ""
        elif days_ago is None or days_ago == "":
            # shop_name で全件数取る
            sqlstr += f''' WHERE shop_name = {shop_name};'''
        elif shop_name is None or shop_name == "":
            # days_ago で全件数取る
            today = get_today_str(0, "YMD")
            start_day = get_today_str(days_ago, "YMD")
            sqlstr += f''' WHERE created_at BETWEEN '{start_day} 00:00:00' AND '{today} 23:59:59';'''
        else:
            # shop_name かつ days_ago
            sqlstr = f"SELECT * FROM Orders WHERE shop_name = '{shop_name}' AND created_at BETWEEN '{start_day} 00:00:00' AND '{today} 23:59:59';"

        print(f"sqlstr: {sqlstr}")

        await cursor.execute(sqlstr)
        rows = await cursor.fetchall()
        #print(f"rows: {rows}")
        if not rows:
            warnings.warn("No order found with the given shopid")
            return None
        else:
            orders = appendOrder(rows)

            orderlist = []
            for o in orders:
                #print("ここまで start")
                #print(f"list: {o}")
                json_data = json.dumps(o, ensure_ascii=False)
                #print(f"json_data: {json_data}")
                dict_data = json.loads(json_data)  # JSON文字列を辞書に変換
                orderlist.append(Order(**dict_data))
                
        return orderlist            
    
    except Exception as e:
        print(f"select_all_orders2 Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()




# 選択
@log_decorator
@deprecated
async def select_all_orders()-> Optional[dict]:
    try:
        conn = await get_connection()
        cursor = await conn.cursor()
        
        sqlstr = f"SELECT * FROM Orders"
        await cursor.execute(sqlstr)
        rows = await cursor.fetchall()
        #print(f"rows: {rows}")
        if not rows:
            warnings.warn("No order found with the given shopid")
        else:
            orders = appendOrder(rows)
            
        return orders
    
    except Exception as e:
        print(f"select_all_orders Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()


# 選択
@deprecated
@log_decorator
async def select_order(username: str)-> Optional[dict]:
    try:
        #print("userid: " + username)
        conn = await get_connection()
        cursor = conn.cursor()
        
        today = get_today_str(0,"YMD")
        
        sqlstr = f"SELECT * FROM Orders WHERE username = '{username}' AND created_at BETWEEN '{today} 00:00:00' AND '{today} 23:59:59';"
        #print(f"sqlstr: {sqlstr}")
        await cursor.execute(sqlstr)
        rows = cursor.fetchall()
        #print("rows: " + str(rows))
        if rows is None:
            warnings.warn("No order found with the given shopid")
        else:
            orders = appendOrder(rows)
        
        print(f"return orders: {orders}")
        
        return orders
    except Exception as e:
        print(f"select_order Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()

# Order辞書を返す
def appendOrder(rows) -> List[dict]:
    orders = []
    for row in rows:
        orders.append({
            "order_id": int(row[0]),
            "company_name": row[1],
            "username": row[2],
            "shop_name": row[3],
            "menu_id": int(row[4]),
            "amount": int(row[5]),
            "created_at": row[6],
            "canceled": bool(row[7])
        })
        #print(f"orderのクラスは {str(type(orders))}")
        #pprint(orders)
        
        # 列名を取得（カラム名をキーにして辞書に変換するため）
        #columns = [column[0] for column in result.description]
        # `Order` クラスにマッピング
        #orders = [Order(**dict(zip(columns, row))) for row in rows]
        
    return orders

# 選択（ユーザーとお弁当屋）
#@log_decorator
async def select_shop_order(shopid: str,
                            days_ago_str: str = None,
                            username: str = None)-> Optional[List[Order]]:
    conn = None
    try:
        #print(f"shopid: {shopid}, days_ago: {days_ago_str}, username: {username}")
        conn = await get_connection()
        cursor = await conn.cursor()

        # ベースクエリ
        #sqlstr = f'''SELECT * FROM Orders WHERE (shop_name = '{shopid}')'''
        # company_idをCompany:nameに変更した
        sqlstr = f'''SELECT O.order_id, C.name AS company_name, O.username, O.shop_name, O.menu_id, O.amount, O.created_at, O.canceled FROM Orders O'''
        sqlstr = sqlstr + ''' INNER JOIN Company C ON O.company_id = C.company_id'''
        sqlstr = sqlstr + f" WHERE (O.shop_name = '{shopid}')"

        # 期間が指定されている場合、条件を追加
        if days_ago_str:
            days_ago = int(days_ago_str)
            start_day = get_today_str(days_ago, "YMD")
            end_day = get_today_str(0, "YMD") # 13時が締め切り

            sqlstr += f''' AND (O.created_at BETWEEN '{start_day} 00:00:00' AND '{end_day} 23:59:59')'''
            #print(f"start day: {start_day}")
            #print(f"today: {end_day}")

        # ユーザーIDが指定されている場合、条件を追加
        if username is None or username == '':
            sqlstr += ""
        else:
            sqlstr += f" AND (O.username = '{username}')"
        
        #print(f"sqlstr: {sqlstr}")
        result = await cursor.execute(sqlstr)
        rows = await result.fetchall()
        #print("ここまで 1")
        #print("rows: " + str(rows))
        
        if rows is None:
            warnings.warn("No order found with the given shopid")
            return None
        else:
            #print("ここまで 2")
            #print(f"rows: {rows}")
            orders = appendOrder(rows)
            
            # ここからList<Order>クラスにキャストする
            #print(f"ordersの型: {str(type(orders))}")
            #print(f"orders.count(): {len(orders)}")
            orderlist = []
            for o in orders:
                #print("ここまで start")
                #print(f"list: {o}")
                json_data = json.dumps(o, ensure_ascii=False)
                #print(f"json_data: {json_data}")
                dict_data = json.loads(json_data)  # JSON文字列を辞書に変換
                orderlist.append(Order(**dict_data))
                #print(orderlist)
                #print("ここまで end")
        #print(f" orderlist: {orderlist}")
        
        return orderlist

    except Exception as e:
        print(f"select_shop_order Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()

# 選択（ユーザーとお弁当屋）
@log_decorator
@deprecated
async def select_today_orders(shopid: str, userid: str = None)-> Optional[dict]:
    conn = None
    try:
        #print(f"shopid: {shopid}, userid: {userid}")
        conn = await get_connection()
        cursor = await conn.cursor()
        today = get_today_str(0,"YMD")

        # ベースクエリ
        sqlstr = '''SELECT * FROM Orders
        WHERE (shop_name = ?) AND (created_at BETWEEN ? AND ?)
        '''
        params = [shopid, f"{today} 00:00:00", f"{today} 23:59:59"]

        # ユーザーIDが指定されている場合、条件を追加
        if userid is not None:
            sqlstr += " AND (username = ?)"
            params.append(userid)
        
        #print(f"sqlstr: {sqlstr}")
        result = await cursor.execute(sqlstr,params)
        rows = await result.fetchall()
        #print("rows: " + str(rows))
        
        if rows is None:
            warnings.warn("No order found with the given shopid")
        else:
            #print(f"rows: {rows}")
            orders = appendOrder(rows)
        #print(f" Shop orders: {orders}")
        return orders

    except Exception as e:
        print(f"select_today_orders Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()

# 注文全確認
@log_decorator
async def show_all_orders():
    try:
        conn = await get_connection()
        cursor = await conn.cursor()
        await cursor.execute('SELECT * FROM Orders')
        rows = await cursor.fetchall()
        for row in rows:
            pprint(row)
    finally:
        await conn.close()

# 追加
@log_decorator
async def insert_order(company_id, username, shop_name, menu_id, amount, created_at=None):
    conn = None
    try:
        conn = await get_connection()
        sql_query = '''
        INSERT INTO Orders (company_id, username, shop_name, menu_id, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        created_at = get_today_str()
        values = (company_id, username, shop_name, menu_id, amount, created_at)
        await conn.execute(sql_query, values)
        await conn.commit()
        #print("注文追加成功")
    except Exception as e:
        print(f"insert_order Error: {e}")
    finally:
        if not conn:
            await conn.close()

# 選択
@log_decorator
async def select_company(company_id: str):
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        sql_query = 'SELECT * FROM Company WHERE company_id = ?'
        params = [company_id]
        await cursor.execute(sql_query, params)
        row = cursor.fetchall()
        return row
    except Exception as e:
        print(f"select_company Error: {e}")
    finally:
        if conn:
            await conn.close()

# メニューテーブル
# 作成
#@log_decorator
async def create_menu_table():
    try:
        conn = await get_connection() 
        if conn is None: 
            print("データベース接続の確立に失敗しました。")
            return    
        #cursor = conn.cursor()
        await conn.execute('''
        CREATE TABLE Menu (
        menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name TEXT,
        name TEXT,
        price INTEGER,
        description TEXT DEFAULT '',
        picture_path TEXT DEFAULT '',
        disabled INTEGER DEFAULT 0,
        created_at TEXT
        )
        ''')
        await conn.commit()
    except Exception as e:
        print(f"create_menu_table Error: {e}")
    finally:
        if conn:
            await conn.close()

# 追加
@log_decorator
# 書式
# insert_menu(shop_name='shop01', name='お昼の定食', price=500, description='お昼のランチお弁当です', picture_path='c:\\picture'もしくはpicture_path=r'c:\\picture')
async def insert_menu(shop_name, name, price, description, picture_path = None):
    try:
        conn = await get_connection()
        #cursor = conn.cursor()

        created_at = get_today_str()
        
        #print(f"menu_id: ""自動連番"", shop_name: {shop_name}, name: {name}, price: {price}, description: {description}, picture_path: {picture_path}, created_at: {created_at}")
        
        sql_query = '''
        INSERT INTO Menu (shop_name, name, price, description, picture_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        values = (shop_name, name, price, description, picture_path, created_at)
        await conn.execute(sql_query, values)

        await conn.commit()
        #print("メニュー追加成功")
    except Exception as e:
        print(f"insert_menu Error: {e}")
    finally:
        if conn:
            await conn.close()
    
# 選択
@log_decorator
async def select_menu(shop_name: str)-> Optional[dict]:
    try:
        #print("shop_name: " + shop_name)
        conn = await get_connection()
        cursor = conn.cursor()

        sqlstr = f"SELECT * FROM Menu WHERE shop_name = '{shop_name}'"
        #print(f"sqlstr: {sqlstr}")
        await cursor.execute(sqlstr)
        rows = cursor.fetchall()
        #print("rows: " + str(rows))
        if rows is None:
            warnings.warn("No menu found with the given shopid")
        else:
            items = appendMenu(rows)
        return items
    
    except Exception as e:
        print(f"select_menu Error: {e}")
        return None
    finally:
        if conn:
            await conn.close()

# 辞書を返す
def appendMenu(rows):
    items = []
    for row in rows:
        items.append({
            "menu_id": row[0],
            "shop_name": row[1],
            "name": row[2],
            "price": row[3],
            "description": row[4],
            "picture_path": row[5],
            "disabled": row[6],
            "created_at": row[7]
        })
        print(f"menuのクラスは {str(type(items))}")
        #pprint(menus)
    return items


'''owari'''

# AUTOINCREMENTフィールドをリセット
#@log_decorator
async def reset_all_autoincrement():
    conn = None
    try:
        conn = await get_connection()
        # AUTOINCREMENT のリセット
        for table in ["Company", "Orders", "Menu"]:
            await conn.execute(f'DELETE FROM sqlite_sequence WHERE name = "{table}"')
        await conn.commit()  # コミットを一度だけ実行
        print("AUTOINCREMENT のリセット完了")
        '''
        cursor = conn.cursor()
        await cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Company"')
        await conn.commit()
        
        #cursor = conn.cursor()
        await cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Orders"')
        await conn.commit()
        
        #cursor = conn.cursor()
        await cursor.execute('DELETE FROM sqlite_sequence WHERE name = "Menu"')
        await conn.commit()
        '''
    except Exception as e:
        print(f"reset_all_autoincrement Error: {e}")
    finally:
        if conn:
            await conn.close()

# 全テーブルをDrop
#@log_decorator
async def drop_all_table():
    conn = None
    try:
        #'DROP TABLE IF EXISTS Company'
        conn = await get_connection()
        # AUTOINCREMENT のリセット
        for table in ["Company", "Orders", "Menu", "User"]:
            await conn.execute(f'DROP TABLE IF EXISTS {table}')
        await conn.commit()  # コミットを一度だけ実行
        print("全テーブルのDrop完了")
    except Exception as e:
        print(f"drop_all_table Error: {e}")
    finally:
        if conn:
            await conn.close()



# 削除
@log_decorator
async def delete_all_company():
    conn = await get_connection()
    cursor = conn.cursor()
    await cursor.execute('DROP TABLE IF EXISTS Company')
    await conn.commit()
    await conn.close()


@log_decorator
async def delete_all_orders():
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        await cursor.execute('DROP TABLE IF EXISTS Orders')
        #await cursor.execute('DELETE FROM Orders')    
        await conn.commit()
    except Exception as e:
        print(f"delete_all_orders Error: {e}")
    finally:
        if conn:
            await conn.close()

@log_decorator
async def delete_all_user():
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        #await cursor.execute('DELETE FROM User')    
        await cursor.execute('DROP TABLE IF EXISTS User')
        await conn.commit()
        await conn.close()
    except Exception as e:    
        print(f"delete_all_user Error: {e}")
    finally:
        if conn:
            await conn.close()

# 削除
@log_decorator
async def delete_all_menu():
    conn = await get_connection()
    cursor = conn.cursor()
    await cursor.execute('DROP TABLE IF EXISTS Menu')
    conn.commit()
    await conn.close()

#@log_decorator
async def init_database():
    try:
        await reset_all_autoincrement()
        await drop_all_table()

        await create_user_table() 
        # 1
        await insert_user("user1", "user1", "大隈 慶1",company_id=1, shop_name="shop01", menu_id=1) 
        # 2
        await insert_user("user2", "user2", "大隈 慶2",company_id=1, shop_name="shop01", menu_id=1)
        # 3
        await insert_shop("shop01", "shop01", "お店shop01")
        
        await create_company_table()
        # 1
        await insert_company("テンシステム", "083-999-9999", "shop01")

        await create_menu_table()
        # 1
        await insert_menu(shop_name='shop01', name='お昼の定食', price=500, description='お昼のランチお弁当です', picture_path='c:\\picture')
        
        await create_orders_table()
        '''INSERT INTO Orders (company_id, username, shop_name, menu_id,  amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)'''
        
        
        # 1
        await insert_order(1, "user1", "shop01", 1, 1, get_today_str(-5))
        # 2
        await insert_order(1, "user2", "shop01", 1, 2, get_today_str(-4))
        # 3
        await insert_order(1, "tenten01", "shop01", 1, 3, get_today_str(-3))
        # 4
        await insert_order(1, "tenten02", "shop01", 1, 1, get_today_str(-2))
        # 5
        await insert_order(1, "user3", "shop01", 1, 1, get_today_str(-1))
        # 6
        await insert_order(1, "user1", "shop02", 1, 1, get_today_str())
        
        
        await show_all_orders()

        
        print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"init_database Error: {str(e)}")
        import traceback 
        traceback.print_exc()
