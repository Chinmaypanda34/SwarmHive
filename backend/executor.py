import requests
import yaml
import json
from jsonpath_ng import parse as jp_parse
from copy import deepcopy

class Executor:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.context = {}  # captured variables

    def _render(self, obj):
        if isinstance(obj, dict):
            return {k: self._render(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._render(v) for v in obj]
        if isinstance(obj, str):
            for k, v in self.context.items():
                obj = obj.replace("{{ " + k + " }}", str(v))
            return obj
        return obj

    def _capture(self, resp_json, capture_map):
        if not capture_map or not resp_json:
            return
        for var, path in capture_map.items():
            try:
                expr = jp_parse(path)
                matches = [m.value for m in expr.find(resp_json)]
                if matches:
                    self.context[var] = matches[0]
            except Exception:
                # ignore capture errors
                pass

    def run_template(self, yaml_text):
        try:
            tpl = yaml.safe_load(yaml_text)
        except Exception as e:
            raise ValueError(f"template YAML parse error: {e}")

        if not tpl or not isinstance(tpl, dict):
            raise ValueError("template is empty or not a YAML mapping (expected dict)")

        results = {"name": tpl.get("name"), "steps": []}
        for step in tpl.get("steps", []):
            if not isinstance(step, dict) or "method" not in step or "path" not in step:
                results["steps"].append({
                    "id": step.get("id") if isinstance(step, dict) else None,
                    "status_code": None,
                    "request": None,
                    "response": None,
                    "ok": False,
                    "error": "invalid step format"
                })
                continue

            method = step["method"].lower()
            path = self._render(step["path"])
            url = self.base_url + path if path.startswith("/") else self.base_url + "/" + path
            body = self._render(step.get("body")) if "body" in step else None
            headers = self._render(step.get("headers")) if "headers" in step else {}

            try:
                resp = self.session.request(method, url, json=body, headers=headers, timeout=15)
            except Exception as e:
                results["steps"].append({
                    "id": step.get("id"),
                    "status_code": None,
                    "request": {"url": url, "method": method.upper(), "body": body, "headers": headers},
                    "response": None,
                    "ok": False,
                    "error": f"request failed: {e}"
                })
                continue

            step_res = {
                "id": step.get("id"),
                "status_code": resp.status_code,
                "request": {"url": url, "method": method.upper(), "body": body, "headers": headers},
                "response": None,
                "ok": True
            }
            try:
                j = resp.json()
                step_res["response"] = j
            except Exception:
                step_res["response"] = resp.text
                j = None

            if "capture" in step:
                self._capture(j, step["capture"])
            if "expect_status" in step:
                step_res["ok"] = (resp.status_code == step["expect_status"])
            results["steps"].append(step_res)

        results["context"] = self.context
        return results

# --------------------------
# detection helpers
# --------------------------
def compare_json(a, b):
    """Return True if JSONs are equal (deep equality)"""
    if a is None or b is None:
        return False
    try:
        return a == b
    except Exception:
        return False

def detect_issues(results):
    findings = []
    
    for step in results.get('steps', []):
        step_id = step.get('id')
        status_code = step.get('status_code')
        response_body = step.get('response', {})
        
        # IDOR Detection
        if step_id == 'userB_access_userA_profile' and status_code == 200:
            findings.append({
                "type": "IDOR",
                "severity": "high",
                "description": "User B can access User A's profile data",
                "step_id": step_id,
                "evidence": f"User B successfully accessed User A's profile: {response_body}"
            })
        
        if step_id == 'userB_modify_userA_profile' and status_code == 200:
            findings.append({
                "type": "IDOR",
                "severity": "high", 
                "description": "User B can modify User A's profile data",
                "step_id": step_id,
                "evidence": f"User B successfully modified User A's profile: {response_body}"
            })
        
        # Broken Access Control
        if step_id == 'regular_user_access_admin' and status_code == 200:
            findings.append({
                "type": "Broken Access Control",
                "severity": "high",
                "description": "Regular user can access admin endpoint",
                "step_id": step_id,
                "evidence": f"Regular user accessed admin data: {response_body}"
            })
        
        # Information Disclosure
        if step_id == 'user_enumeration' and status_code == 200:
            if "not found" in str(response_body).lower():
                findings.append({
                    "type": "Information Disclosure",
                    "severity": "medium",
                    "description": "User enumeration vulnerability - reveals if user exists",
                    "step_id": step_id,
                    "evidence": f"Response reveals user doesn't exist: {response_body}"
                })
    
    return findings