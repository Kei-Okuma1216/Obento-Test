import asyncio
import sqlite3
from typing import Optional

from fastapi import Request

# データベース初期化
# インメモリデータベースを作成
#conn = sqlite3.connect(':memory:')

def get_connection(): 
     conn = sqlite3.connect('example.db') 
     # データベースファイル名を指定 
     return conn

def init_database():
    
    try:
          conn = get_connection()
          if conn is None: 
               print("データベース接続の確立に失敗しました。")
          #cursor = conn.cursor()
          #create_user_table(cursor) 
          insert_mock_user(conn, "k.okuma", "aaa", 1)
          insert_mock_user(conn, "k.okuma@ten-system.com", "aaa12345", 3)
          print('A'+ str(conn))
          conn.close() 
          print("データベースファイル 'sample.db' が正常に作成されました。")
    except sqlite3.Error as e: 
         print(f"SQLiteエラー: {e}")
    except Exception as e: 
        print(f"Error: {str(e)}")
        import traceback 
        traceback.print_exc()
     
# テーブルを作成
def create_user_table(cursor):
     cursor.execute('''
     CREATE TABLE User (
     userid TEXT PRIMARY KEY,
     password TEXT,
     token TEXT,
     permission INTEGER
     )
     ''')

# コネクションを閉じる（実際のテストでは不要）
#conn.close()

# テスト用の偽ユーザーを追加する関数
def insert_mock_user(conn, userid, password, permission):
    #conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO User (userid, password, permission)
    VALUES (?, ?, ?)
    ''', (userid, password, permission))
    conn.commit()


async def select_mock_user(userid: str, request: Request)-> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        print("SELECT前")
        cursor.execute('SELECT * FROM User WHERE userid = ?', (userid,))
        row = cursor.fetchone()  # または fetchall() を使用
        print("SELECT後")
        if row is None:
                raise ValueError("No user found with the given userid")
        # 結果を辞書形式に変換        
        print("row[0]: " + row[0])
        if row:
            result = {
                "userid": row[0],
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



# データの確認
def show_all_users(cursor):
     conn = get_connection()
     cursor = conn.cursor()
     cursor.execute('SELECT * FROM User')
     rows = cursor.fetchall()
     for row in rows:
          print(row)
     conn.close()