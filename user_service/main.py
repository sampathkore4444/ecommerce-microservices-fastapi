from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(title="User Service", version="1.0.0")

{
    "username": "Ramana1",
    "password": "123451",
    "full_name": "Ramana Kumar1",
    "email": "Ramana@gmail.com1",
}

{
    "username": "Ramana2",
    "password": "123451",
    "full_name": "Ramana Kumar",
    "email": "Ramana@gmail.com",
}

# In-memory database
users_db = {}


# Models
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    created_at: datetime


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None


# Routes
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())

    user_data = {
        "id": user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "password": user.password,
        "created_at": datetime.now(),
    }

    # Save to database
    users_db[user_id] = user_data

    return user_data


@app.get("/users/", response_model=List[UserResponse])
async def get_all_users():
    print(f"Database contents: {users_db}")  # See everything
    print(f"Keys: {list(users_db.keys())}")  # See just keys
    return list(users_db.values())


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    if user_id not in users_db:
        return HTTPException(status_code=404, detail="User does not exist")
    else:
        return users_db[user_id]


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    if user_id not in users_db:
        return HTTPException(status_code=404, detail="User does not exist")
    else:
        user_data = users_db[user_id]
        print("user_data====", user_data)

        print("user_update.email====", user_update.email)
        print("user_update.full_name====", user_update.full_name)

        if user_update.email is not None:
            user_data["email"] = user_update.email

        if user_update.full_name is not None:
            user_data["full_name"] = user_update.full_name

        # Save back to database
        users_db[user_id] = user_data

        return user_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
