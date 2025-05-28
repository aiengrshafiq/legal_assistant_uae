from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from app.auth.database import SessionLocal
from app.auth.models import QueryLog

from fastapi import Request, HTTPException, Depends

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.database import get_db

from sqlalchemy.exc import SQLAlchemyError
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def log_query(user_email, username, module, question, response):
    try:
       
        db = SessionLocal()

        # 🛠 Safely convert response to string if it's a dict
        if isinstance(response, dict):
            response = json.dumps(response)

        log = QueryLog(
            email=user_email,
            username=username,
            module=module,
            question=question,
            response=response[:3000],  # Truncate to avoid DB size issues
        )
        db.add(log)
        db.commit()
        db.refresh(log)
    except SQLAlchemyError as e:
        import logging
        logging.exception("❌ Failed to log query")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token decode error")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user