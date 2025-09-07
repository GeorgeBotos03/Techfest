import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

 integrate-fraud-ai
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/antiscam",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/antiscam")

# pool mic e suficient pt. demo
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

 main
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
