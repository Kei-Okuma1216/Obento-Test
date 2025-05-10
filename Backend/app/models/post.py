from sqlalchemy import Column, Integer, String
from database.local_postgresql_database import Base

class Post(Base):
    __tablename__ = "posts"
    __table_args__ = {"schema": "public"}  # ★ 追加：スキーマ指定
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)

# alembic revision --autogenerate -m "create posts table"
