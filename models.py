from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user") # user, expert, admin
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class ExpertProfile(Base):
    __tablename__ = "expert_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    category: Mapped[str] = mapped_column(String(80))
    bio: Mapped[str] = mapped_column(String(1000), default="")
    credentials_note: Mapped[str] = mapped_column(String(500), default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expert_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_paise: Mapped[int] = mapped_column(Integer, default=10000)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")
    status: Mapped[str] = mapped_column(String(20), default="requested")
    # Access is granted only after verified payment webhook in production.
