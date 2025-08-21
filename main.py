from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Prescription
import crud, schemas
from reminder import scheduler
from call_utils import make_call
from email_utils import send_email

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Medicine Reminder API")

@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# ✅ Test calling endpoint
@app.post("/test/call")
def test_call(phone: str, message: str = "This is a test call from Medicine Reminder system."):
    make_call(phone, message)
    return {"status": "Call initiated", "to": phone, "message": message}

# ✅ Test email endpoint
@app.post("/test/email")
def test_email(email: str, message: str = "This is a test email from Medicine Reminder system."):
    send_email(email, "Test Reminder", message)
    return {"status": "Email sent", "to": email, "message": message}
