from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User
from shared.schemas import UserCreate, UserResponse
from dependencies import get_current_active_user

from ..event_handlers import publish_user_registered


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_password = User.get_password_hash(user.password)

    # Create new user instance
    new_user = User(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh to get the auto-generated ID

    # 🎯 MESSAGE QUEUE: Publish event asynchronously
    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        hashed_password=new_user.hashed_password,
        created_at=new_user.created_at,
    )

    # Publish user registration event
    await publish_user_registered(user_response.dict())

    # return new_user  # FastAPI automatically converts to UserResponse
    return user_response


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user  # FastAPI automatically converts to UserResponse


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user  # FastAPI automatically converts to UserResponse
