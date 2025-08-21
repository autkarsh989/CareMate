from sqlalchemy.orm import Session
from models import User, Prescription
from schemas import UserCreate

def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password=user.password,
        reminder_type=user.reminder_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    for pres in user.prescriptions:
        db_pres = Prescription(
            medicine_name=pres.medicine_name,
            dosage=pres.dosage,
            timings=pres.timings,
            user_id=db_user.id
        )
        db.add(db_pres)

    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(User).all()

def get_prescriptions(db: Session):
    return db.query(Prescription).all()
