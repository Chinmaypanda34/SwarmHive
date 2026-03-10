from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Simple in-memory database
users_db = {
    "userA": {"id": 1, "password": "Password123", "token": "tokenA"},
    "userB": {"id": 2, "password": "Password123", "token": "tokenB"}
}

profiles_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "ssn": "123-45-6789"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com", "ssn": "987-65-4321"}
}

class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateRequest(BaseModel):
    email: str
    name: str

class ResetPasswordRequest(BaseModel):
    username: str

# Helper function to get current user
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization required")
    
    token = authorization.replace("Bearer ", "")
    
    # Find user by token
    current_user = None
    for username, user_data in users_db.items():
        if user_data["token"] == token:
            current_user = user_data
            break
    
    if not current_user:
        raise HTTPException(401, "Invalid token")
    
    return current_user

@app.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.username)
    if user and user["password"] == req.password:
        return {"token": user["token"], "user_id": user["id"]}
    raise HTTPException(401, "Invalid credentials")

# FIXED: Added ownership check
@app.get("/users/{user_id}/profile")
async def get_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    # Check if the requested profile belongs to the current user
    if current_user["id"] != user_id:
        raise HTTPException(403, "Access denied")
    
    if user_id in profiles_db:
        return profiles_db[user_id]
    raise HTTPException(404, "Profile not found")

# FIXED: Added ownership check
@app.put("/users/{user_id}/profile")
async def update_profile(user_id: int, req: UpdateRequest, current_user: dict = Depends(get_current_user)):
    # Check if the requested profile belongs to the current user
    if current_user["id"] != user_id:
        raise HTTPException(403, "Access denied")
    
    if user_id in profiles_db:
        profiles_db[user_id]["email"] = req.email
        profiles_db[user_id]["name"] = req.name
        return {"message": "Profile updated", "profile": profiles_db[user_id]}
    raise HTTPException(404, "Profile not found")

# FIXED: Added admin check (you'd need to add admin role to users_db)
@app.get("/admin/users")
async def admin_users(current_user: dict = Depends(get_current_user)):
    # In a real app, check if user has admin role
    # For now, let's assume only user with id 1 is admin
    if current_user["id"] != 1:
        raise HTTPException(403, "Admin access required")
    
    return {"users": list(profiles_db.values())}

# FIXED: Prevent username enumeration
@app.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    # Always return the same message regardless of user existence
    return {"message": "If an account with that username exists, a reset email has been sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)