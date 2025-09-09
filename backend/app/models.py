from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column, Integer, String, BigInteger, TIMESTAMP, ForeignKey,
    Boolean, JSON, Float, text
)

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(64), unique=True)
    name = Column(String)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    iban = Column(String(34), unique=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(BigInteger, primary_key=True)
    ts = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    src_account_id = Column(Integer, ForeignKey("accounts.id"))
    dst_account_id = Column(Integer, nullable=True)
    dst_iban = Column(String(34), nullable=True)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    channel = Column(String(16), nullable=False)  # web|mobile|branch
    is_first_to_payee = Column(Boolean, default=False)
    device_fp = Column(String(128), nullable=True)
    risk_score = Column(Float, default=0)
    risk_reasons = Column(JSON, default=list)
    action = Column(String(16), default="allow")
