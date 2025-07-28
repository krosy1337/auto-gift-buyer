from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, Float, func, UniqueConstraint
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    balance = Column(Integer, default=0)
    business_connection = Column(String, nullable=True)

    profiles = relationship("AutobuyProfile", backref="user", cascade="all, delete-orphan")
    purchases = relationship("GiftPurchase", backref="user", cascade="all, delete-orphan")
    collections = relationship("UserCollection", backref="user", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = 'collections'
    id = Column(String, primary_key=True)


class UserCollection(Base):
    __tablename__ = "user_collections"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    collection_id = Column(String, ForeignKey("collections.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("autobuy_profiles.id"), nullable=True)

    gifts_bought = Column(Integer, default=0)
    completed = Column(Boolean, default=False)

    collection = relationship("Collection", backref="user_collections")
    profile = relationship("AutobuyProfile", backref="user_collections")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    telegram_payment_charge_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Refund(Base):
    __tablename__ = "refunds"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    refunded_at = Column(DateTime, default=datetime.utcnow)


class GiftPurchase(Base):
    __tablename__ = "gift_purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    collection_id = Column(String, ForeignKey("collections.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("autobuy_profiles.id"), nullable=True)

    gift_star_cost = Column(Integer, nullable=False)

    collection = relationship("Collection", backref="gift_purchases")
    profile = relationship("AutobuyProfile", backref="gift_purchases")


class AutobuyProfile(Base):
    __tablename__ = "autobuy_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    min_stars = Column(Integer, default=0)
    max_stars = Column(Integer, default=None)
    supply_limit = Column(Integer, default=None)
    purchase_cycles = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)
    channel_username = Column(String, nullable=True)
