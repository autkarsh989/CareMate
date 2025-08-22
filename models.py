from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    password = Column(String)
    reminder_type = Column(String, default="both")  # email, call, both

    prescriptions = relationship("Prescription", back_populates="user")
    user_text = relationship("UserText", back_populates="user", uselist=False)

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String)
    dosage = Column(String)
    timings = Column(String)  # "09:00,14:00,21:00"
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="prescriptions")


class UserText(Base):
    __tablename__ = "user_texts"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    text = Column(String)

    user = relationship("User", back_populates="user_text")
