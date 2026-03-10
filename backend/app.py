import requests.exceptions
import uuid, os, json, pathlib, yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from copy import deepcopy
from starlette.middleware.cors import CORSMiddleware 
from report_generator import router as report_router
from spiderfoot_integration import router as spiderfoot_router

from discovery import load_openapi_from_url, list_endpoints_from_spec
from executor import Executor, detect_issues

APP_DIR = pathlib.Path(__file__).parent.resolve()
SPECS_DIR = APP_DIR / "specs"
SPECS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR = APP_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)
RUN_DIR = APP_DIR / "results"
RUN_DIR.mkdir(exist_ok=True)

app = FastAPI()

# Add CORS middleware to allow the frontend to communicate with the backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(report_router, prefix="/api")
app.include_router(spiderfoot_router, prefix="/api")

# In-memory index: spec_id -> spec (loaded from disk at startup)
SPECS = {}

def persist_spec(spec_id: str, spec_obj):
    """Write spec_obj (dict) to specs/<spec_id>.json on disk."""
    path = SPECS_DIR / f"{spec_id}.json"
    with open(path, "w", encoding="utf8") as f:
        json.dump(spec_obj, f, indent=2)

def load_persisted_specs():
    """Load all specs/*.json into SPECS at startup."""
    for p in SPECS_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf8") as f:
                spec = json.load(f)
            spec_id = p.stem
            SPECS[spec_id] = spec
        except Exception:
            # ignore malformed spec files but continue
            continue

# load persisted specs on startup
load_persisted_specs()

class UploadSpec(BaseModel):
    url: str

class DryRunReq(BaseModel):
    template: str
    target_base: str

class RunTemplateReq(BaseModel):
    spec_id: str
    template: str
    target_base: str
    consent: bool = False

@app.post("/api/upload_spec")
def upload_spec(body: UploadSpec):
    try:
        spec_url = body.url
        if not spec_url.endswith("/openapi.json"):
            spec_url = spec_url.rstrip('/') + '/openapi.json'
        
        spec = load_openapi_from_url(spec_url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=400, detail="Could not find OpenAPI spec at the provided URL.")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    spec_id = str(uuid.uuid4())
    SPECS[spec_id] = spec
    try:
        persist_spec(spec_id, spec)
    except Exception:
        pass
    endpoints = list_endpoints_from_spec(spec)
    return {"spec_id": spec_id, "endpoints": endpoints}

@app.get("/api/specs")
def list_specs():
    out = []
    for spec_id, spec in SPECS.items():
        info = {"spec_id": spec_id}
        info["title"] = spec.get("info", {}).get("title") if isinstance(spec, dict) else None
        out.append(info)
    return out

@app.get("/api/specs/{spec_id}")
def get_spec(spec_id: str):
    spec = SPECS.get(spec_id)
    if not spec:
        raise HTTPException(404, "spec not found")
    return spec

@app.get("/api/specs/{spec_id}/endpoints")
def get_endpoints(spec_id: str):
    spec = SPECS.get(spec_id)
    if not spec:
        raise HTTPException(404, "spec not found")
    return list_endpoints_from_spec(spec)

@app.get("/api/templates")
def list_templates():
    templates = {}
    for p in TEMPLATES_DIR.glob("*.yaml"):
        with open(p, "r", encoding="utf8") as f:
            templates[p.name] = f.read()
    return templates

@app.post("/api/dry_run")
def dry_run(req: DryRunReq):
    try:
        tpl = yaml.safe_load(req.template)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"template YAML parse error: {e}")
    if not tpl or not isinstance(tpl, dict):
        raise HTTPException(status_code=400, detail="template is empty or invalid")

    steps = []
    base = req.target_base.rstrip("/")
    for step in tpl.get("steps", []):
        if not isinstance(step, dict):
            continue
        path = step.get("path", "")
        url = base + path if path.startswith("/") else base + "/" + path
        steps.append({
            "id": step.get("id"),
            "method": step.get("method"),
            "path": path,
            "url": url,
            "body": step.get("body", None),
            "headers": step.get("headers", None),
            "expect_status": step.get("expect_status", None),
            "destructive": (step.get("method","").upper() in ["POST","PUT","DELETE","PATCH"])
        })
    return {"name": tpl.get("name"), "steps": steps}

@app.post("/api/run_template")
def run_template(req: RunTemplateReq):
    spec = SPECS.get(req.spec_id)
    if not spec:
        raise HTTPException(404, "spec not found")
    
    try:
        tpl = yaml.safe_load(req.template)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"template YAML parse error: {e}")

    destructive = False
    for step in tpl.get("steps", []):
        if isinstance(step, dict) and step.get("method","").upper() in ["POST","PUT","DELETE","PATCH"]:
            destructive = True
            break

    if destructive and not req.consent:
        raise HTTPException(status_code=403, detail="Template contains destructive steps; consent required to run.")

    execr = Executor(req.target_base)
    try:
        results = execr.run_template(req.template)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    try:
        findings = detect_issues(results)
        results["findings"] = findings
    except Exception:
        results["findings"] = []

    run_id = str(uuid.uuid4())
    with open(RUN_DIR / f"{run_id}.json", "w", encoding="utf8") as f:
        json.dump(results, f, indent=2)
    return {"run_id": run_id}

@app.get("/api/results/{run_id}")
def get_results(run_id: str):
    path = RUN_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(404, "run not found")
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)