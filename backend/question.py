from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(JSON)        # 去掉 default=[]
    answer = Column(String(50), nullable=False)
    difficulty = Column(Integer, default=2)
    knowledge_point = Column(String(100), default="")
    chapter = Column(Integer, default=1)
    analysis = Column(Text)       # 去掉 default=""
    ks = Column(JSON)             # 去掉 default=[]
    created_at = Column(DateTime, default=datetime.now)