# test_api.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Creds(BaseModel):
    username: str
    password: str

# simple login returns fixed token
@app.post("/login")
async def login(creds: Creds):
    # demo: accept anything and return fixed token
    return {"token": "abc123"}

# protected endpoint requires that token
@app.get("/users/2/profile")
async def profile(request: Request):
    auth = request.headers.get("authorization", "")
    if auth != "Bearer abc123":
        raise HTTPException(status_code=403, detail="forbidden")
    return {"id": 2, "name": "Alice Example", "email": "alice@example.com"}