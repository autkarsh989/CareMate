from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Prescription
import crud, schemas
from call_utils import make_call
from email_utils import send_email

from config import GEMINI_API_KEY
import requests

from reminder import reminder_queue, producer, consumer
import threading
from apscheduler.schedulers.background import BackgroundScheduler


# JWT and password hashing setup
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Medicine Reminder API")
scheduler=None

@app.on_event("startup")
def start_services():
    # Start the consumer thread (runs forever)
    threading.Thread(target=consumer, daemon=True).start()

    # Schedule the producer to run every minute
    scheduler = BackgroundScheduler()
    scheduler.add_job(producer, "cron", minute="*")
    scheduler.start()
    app.state.scheduler = scheduler


# Utility functions for authentication
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


# Registration endpoint (hash password before saving)
@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    user.password = get_password_hash(user.password)
    return crud.create_user(db, user)

# Login endpoint
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# @app.get("/users/", response_model=list[schemas.UserOut])
# def list_users(db: Session = Depends(get_db)):
#     return crud.get_users(db)

# Protected endpoint example: only logged-in users can add medicine
@app.post("/prescriptions/add")
def add_prescription(prescription: schemas.PrescriptionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_pres = Prescription(
        medicine_name=prescription.medicine_name,
        dosage=prescription.dosage,
        timings=prescription.timings,
        user_id=current_user.id
    )
    db.add(db_pres)
    db.commit()
    db.refresh(db_pres)
    return db_pres

# ✅ Test calling endpoint
@app.post("/test/call")
def test_call(
    phone: str = Body(...),
    message: str = Body("This is a test call from Medicine Reminder system.")
):
    make_call(phone, message)
    return {"status": "Call initiated", "to": phone, "message": message}

# ✅ Test email endpoint

@app.post("/test/email")
def test_email(
    email: str = Body(...),
    message: str = Body("This is a test email from Medicine Reminder system.")
):
    send_email(email, "Test Reminder", message)
    return {"status": "Email sent", "to": email, "message": message}



# New endpoint: Add text to user-specific database row
@app.post("/user/text")
def add_text_to_user_db(
    text: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        user_text = crud.add_or_append_user_text(db, current_user.id, text)
        return {"status": "success", "user_id": current_user.id, "added_text": text, "full_text": user_text.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to database: {e}")


# New endpoint: Ask a question using user's stored text and Gemini AI
@app.post("/user/ask")
def ask_question(
    question: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_text_obj = crud.get_user_text(db, current_user.id)
    user_text = user_text_obj.text if user_text_obj and user_text_obj.text else ""
    prompt = f"User's notes: {user_text}\nQuestion: {question}"
    
    # Call Gemini AI (replace with actual API endpoint and key)
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    # GEMINI_API_KEY = "gemini-key"  # Put your Gemini API key here
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=payload, headers=headers)
        response.raise_for_status()
        ai_answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(ai_answer)
        return {"answer": ai_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {e}")
    
@app.get("/queue-status")
def queue_status():
    return {"queue_size": reminder_queue.qsize()}