import sqlite3

# SQLiteデータベースに接続（データベースが存在しない場合は自動的に作成されます）
conn = sqlite3.connect('test.db')

# カーソルオブジェクトを作成
cursor = conn.cursor()

# テーブルを作成するためのSQL文
create_table_query = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER
)
'''

# テーブルを作成
cursor.execute(create_table_query)

# データを挿入
insert_data_query = '''
INSERT INTO users (name, age)
VALUES ('Alice', 30), ('Bob', 25)
'''

cursor.execute(insert_data_query)

# データをコミット（保存）
conn.commit()

# データを取得して表示
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()
for row in rows:
    print(row)

# 接続を閉じる
conn.close()

# 実行方法 コマンドラインで実行
# python dbase.py
