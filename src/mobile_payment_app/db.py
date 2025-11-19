"""Database setup for the mobile_payment_app.

Provides a SQLAlchemy engine and SessionLocal factory plus an init_db helper
that creates tables defined in `models.py`.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .orm_models import Base
import os

# Use a file-based SQLite DB by default (project root). Can be overridden by
# setting MOBILE_PAYMENTS_DATABASE_URL environment variable.
DATABASE_URL = os.environ.get("MOBILE_PAYMENTS_DATABASE_URL", "sqlite:///mobile_payments.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
