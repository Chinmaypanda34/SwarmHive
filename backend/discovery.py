# discovery.py
import requests, yaml

def load_openapi_from_url(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    content_type = r.headers.get("content-type","")
    if "application/json" in content_type or url.endswith(".json"):
        spec = r.json()
    else:
        spec = yaml.safe_load(r.text)
    return spec

def list_endpoints_from_spec(spec):
    paths = spec.get("paths", {})
    endpoints = []
    for path, methods in paths.items():
        for method, meta in methods.items():
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "summary": meta.get("summary","")
            })
    return endpoints
