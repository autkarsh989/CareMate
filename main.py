from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Prescription
import crud, schemas
from reminder import scheduler
from call_utils import make_call
from email_utils import send_email


# JWT and password hashing setup
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Medicine Reminder API")

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
@app.post("/users/", response_model=schemas.UserOut)
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
def test_call(phone: str, message: str = "This is a test call from Medicine Reminder system."):
    make_call(phone, message)
    return {"status": "Call initiated", "to": phone, "message": message}

# ✅ Test email endpoint
@app.post("/test/email")
def test_email(email: str, message: str = "This is a test email from Medicine Reminder system."):
    send_email(email, "Test Reminder", message)
    return {"status": "Email sent", "to": email, "message": message}


# New endpoint: Add text to user-specific file
@app.post("/user/text")
def add_text_to_user_file(
    text: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    import os
    folder = "user_texts"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"user_{current_user.id}.txt")
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        return {"status": "success", "file": file_path, "added_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to file: {e}")
