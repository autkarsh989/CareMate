from pydantic import BaseModel, EmailStr
from typing import List

class PrescriptionBase(BaseModel):
    medicine_name: str
    dosage: str
    timings: str

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionOut(PrescriptionBase):
    id: int
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    reminder_type: str = "both"

class UserCreate(UserBase):
    prescriptions: List[PrescriptionCreate] = []

class UserOut(UserBase):
    id: int
    prescriptions: List[PrescriptionOut] = []
    class Config:
        orm_mode = True
