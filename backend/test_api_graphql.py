# test_api_graphql.py (Vulnerable version for GraphQL)
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# In-memory GraphQL-like data
users = {
    "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
    "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
}

# VULNERABILITY: This endpoint simulates a GraphQL API that
# exposes introspection by default.
@app.post("/graphql")
async def graphql(query: dict):
    if "query" in query and "__schema" in query["query"]:
        # This is the vulnerability. It's a hardcoded, public schema response.
        schema = {
            "data": {
                "__schema": {
                    "types": [
                        {"name": "User", "kind": "OBJECT"},
                        {"name": "Query", "kind": "OBJECT"},
                        {"name": "String", "kind": "SCALAR"}
                    ]
                }
            }
        }
        return JSONResponse(content=schema)

    # Simple mock user query for demonstration
    if "query" in query and "user" in query["query"]:
        user_id = query["query"].split('(')[1].split(')')[0]
        user = users.get(user_id)
        if user:
            return JSONResponse(content={"data": {"user": user}})

    return JSONResponse(content={"errors": [{"message": "Query not supported."}]}, status_code=400)