# test_client.py
import requests, json, sys
BODY = {
  "spec_id": sys.argv[1],
  "template": open(sys.argv[2]).read(),
  "target_base": sys.argv[3]
}
r = requests.post("http://localhost:8000/api/run_template", json=BODY)
print("run response:", r.status_code, r.text)
if r.status_code == 200:
    run_id = r.json().get("run_id")
    print("fetching results...")
    rr = requests.get(f"http://localhost:8000/api/results/{run_id}")
    print(json.dumps(rr.json(), indent=2))
