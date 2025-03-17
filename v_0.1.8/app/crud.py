# crud.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from models import User
from passlib.context import CryptContext
from user_schemas import UserResponse


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードをハッシュ化
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# パスワードを検証
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



# ユーザーを取得
'''async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    return user  # ✅ SQLAlchemyのUserオブジェクトを返す
'''

def get_user(db: Session, user_id: int) -> UserResponse:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        return None
    
    # SQLAlchemy の User モデルから Pydantic モデルに変換
    return UserResponse.model_validate(user) 

# ユーザーを作成
async def create_user(db: AsyncSession, username: str, password: str, name: str):
    hashed_password = hash_password(password)
    db_user = User(username=username, password=hashed_password, name=name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
