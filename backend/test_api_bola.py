# test_api_bola.py (Corrected and fully vulnerable version for BOLA)
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class Creds(BaseModel):
    username: str
    password: str

class Resource(BaseModel):
    name: str
    data: str

# In-memory storage for users and resources to simulate a database
users = {
    "owner": {"id": 101, "token": "token_owner"},
    "attacker": {"id": 102, "token": "token_attacker"},
}
resources = {}

@app.post("/login")
async def login(creds: Creds):
    if creds.username in users:
        return {"token": users[creds.username]["token"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/resources")
async def create_resource(request: Request, resource: Resource):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    if token != users["owner"]["token"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    resource_id = str(uuid.uuid4())
    resources[resource_id] = {
        "owner_id": users["owner"]["id"],
        "name": resource.name,
        "data": resource.data
    }
    return {"id": resource_id, **resources[resource_id]}

# This endpoint is VULNERABLE to BOLA
@app.put("/resources/{resource_id}")
async def update_resource(request: Request, resource_id: str, resource: Resource):
    token = request.headers.get("authorization", "").replace("Bearer ", "")

    # VULNERABILITY: No check is performed here. Any valid token will pass.

    if resource_id not in resources:
        raise HTTPException(status_code=404, detail="Resource not found")

    # The vulnerability: The code does not check if the current user is the owner
    resources[resource_id]["data"] = resource.data
    return {"message": "Resource updated successfully"}