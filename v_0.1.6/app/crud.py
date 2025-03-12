from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードをハッシュ化
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# パスワードを検証
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ユーザーを取得
async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    return user  # ✅ SQLAlchemyのUserオブジェクトを返す

# ユーザーを作成
async def create_user(db: AsyncSession, username: str, password: str, name: str):
    hashed_password = hash_password(password)
    db_user = User(username=username, password=hashed_password, name=name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
