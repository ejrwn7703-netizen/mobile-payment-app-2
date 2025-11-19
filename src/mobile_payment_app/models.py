from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    provider_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KRW")
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)