from datetime import datetime, timedelta,timezone
from typing import Annotated
import jwt
from fastapi import Depends,FastAPI,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from database import init_db, get_user, create_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

init_db()

SECRET_KEY = "your_secret_key_change_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class UserCreate(BaseModel):
    username: str 
    password: str 
    full_name: str | None = None

class UserPublic(BaseModel):
    username: str
    full_name: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str 

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")
authentication_method = HTTPBearer()

app=FastAPI()

def get_password_hash(password:str) -> str:
    return password_hash.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str) -> dict| None:
    user = get_user(username)
    if not user:
        verify_password(password, DUMMY_HASH) 
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(authentication_method)
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(username)
    if not user:
        raise credentials_exception
    return UserPublic(
        username=user["username"],
        full_name=user.get("full_name")
    )

@app.post("/register", status_code=201, summary="Create a new user")
def register_user(body:UserCreate):
    hashed = get_password_hash(body.password)
    create_user(body.username,hashed,body.full_name or "")
    return {"message":"User Registered Successfully"}

@app.post("/login", response_model=Token)
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401,detail="Invalid Credentials")
    access_token = create_access_token({"sub":user["username"]})
    return {"access_token":access_token,"token_type":"bearer"}

@app.get("/me", response_model=UserPublic, summary="Get my profile(protected)")
def read_me(current_user:UserPublic=Depends(get_current_user)):
    return current_user


