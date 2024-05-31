import logging
from datetime import timedelta, datetime, UTC
from typing import Annotated

from fastapi import APIRouter, WebSocket, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status

from config import Session
from models import User, Player

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
SECRET_KEY = 'super secret key'
ALGORITHM = 'HS256'

logging.getLogger('passlib').setLevel(logging.ERROR)
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class CreateUserRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request: CreateUserRequest):
    user = db.query(User).filter(User.username == request.username).first()
    if user:
        raise HTTPException(status_code=409, detail="Username already exists")
    create_user_model = User(
        username=request.username,
        hashed_password=bcrypt_context.hash(request.password)
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(from_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(from_data.username, from_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expire = datetime.now(UTC) + expires_delta
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        return Player(username=username, user_id=user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")


async def get_websocket_user(websocket: WebSocket):
    token = websocket.query_params.get('token')
    if token is None:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token")
    return await get_current_user(token)
