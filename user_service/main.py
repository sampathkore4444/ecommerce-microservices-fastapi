# In-memory database
# users_db = {}


# Models
# class UserCreate(BaseModel):
#     username: str
#     password: str
#     full_name: str
#     email: str


# class UserResponse(BaseModel):
#     id: str
#     username: str
#     full_name: str
#     email: str
#     created_at: datetime


# class UserUpdate(BaseModel):
#     email: Optional[str] = None
#     full_name: Optional[str] = None


# # Routes
# @app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     # Check if user exists

#     user_id = str(uuid.uuid4())

#     user_data = {
#         "id": user_id,
#         "username": user.username,
#         "full_name": user.full_name,
#         "email": user.email,
#         "password": user.password,
#         "created_at": datetime.now(),
#     }

#     # Save to database
#     users_db[user_id] = user_data

#     return user_data


# @app.get("/users/", response_model=List[UserResponse])
# async def get_all_users():
#     print(f"Database contents: {users_db}")  # See everything
#     print(f"Keys: {list(users_db.keys())}")  # See just keys
#     return list(users_db.values())


# @app.get("/users/{user_id}", response_model=UserResponse)
# async def get_user(user_id: str):
#     if user_id not in users_db:
#         return HTTPException(status_code=404, detail="User does not exist")
#     else:
#         return users_db[user_id]


# @app.put("/users/{user_id}", response_model=UserResponse)
# async def update_user(user_id: str, user_update: UserUpdate):
#     if user_id not in users_db:
#         return HTTPException(status_code=404, detail="User does not exist")
#     else:
#         user_data = users_db[user_id]
#         print("user_data====", user_data)

#         print("user_update.email====", user_update.email)
#         print("user_update.full_name====", user_update.full_name)

#         if user_update.email is not None:
#             user_data["email"] = user_update.email

#         if user_update.full_name is not None:
#             user_data["full_name"] = user_update.full_name

#         # Save back to database
#         users_db[user_id] = user_data

#         return user_data


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from database import Base, engine
from routers import auth, users

from monitoring import monitor_app


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Service",
    version="1.0.0",
    description="User management and authentication service",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)

# 🔍 THIS IS THE MONITORING SETUP
monitor_app(app, "user_service")
# What it does:
# 1. Sets up Prometheus metrics collection
# 2. Adds request/response monitoring middleware
# 3. Creates /metrics endpoint for monitoring systems
# 4. Enables performance tracking


# ✅ HEALTH CHECK ENDPOINT
@app.get("/health")
async def health_check():
    """
    Simple health check for load balancers and monitoring
    This is a BASIC health check - just returns status
    """
    return {"status": "healthy", "service": "user_service"}


# ✅ ENHANCED HEALTH CHECK (optional)
@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check including database connectivity
    and other dependencies
    """
    try:
        # Check database connection
        from database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")  # Simple database check
        db.close()

        return {
            "status": "healthy",
            "service": "user_service",
            "database": "connected",
            "timestamp": "2024-01-01T12:00:00Z",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "user_service",
            "database": "disconnected",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
