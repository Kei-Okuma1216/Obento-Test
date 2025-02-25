from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models2 import User

def init_database2():
    engine = create_engine('sqlite:///example2.db', echo=False)
    #Base = declarative_base()
    
    # SQLiteのデータベースを作成
    #Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # INSERT文
    new_user = User(name="John Doe", password="password123", permission=1, token="token_value")

    # データベースに追加
    session.add(new_user)
    session.commit()

    for r in session.query(User).order_by(User.id):
        print(r.id, r.name, r.user_id, r.password, r.permission, r.token, r.exp)

    session.close()