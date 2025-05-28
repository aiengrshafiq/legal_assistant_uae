from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    username = Column(String,nullable=True)
    module = Column(String)
    question = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
