import sqlite3

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
          cursor = conn.cursor()
          create_user_table(cursor) 
          insert_mock_user(conn, "k.okuma", "aaa", "", 1)
          insert_mock_user(conn, "k.okuma@ten-system.com", "aaa12345", "", 3)
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO User (userid, password, permission)
    VALUES (?, ?, ?)
    ''', (userid, password, permission))
    conn.commit()


def select_mock_user(userid):
     conn = get_connection()
     cursor = conn.cursor()
     print("手前")
     result = cursor.execute('SELECT * FROM User')
     print("後")
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