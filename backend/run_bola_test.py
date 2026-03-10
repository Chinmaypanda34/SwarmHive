import requests
import json
import sys
import yaml

spec_id = "fc0f2f01-ad62-4e4e-914a-783cdd35eabd"
template_path = "templates/bola_update.yaml"
target_base = "http://127.0.0.1:9001"
consent = True

try:
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
except FileNotFoundError:
    print(f"Error: Template file not found at {template_path}")
    sys.exit(1)

body = {
    "spec_id": spec_id,
    "template": template_content,
    "target_base": target_base,
    "consent": consent
}

try:
    print("Starting BOLA test...")
    response = requests.post(
        "http://127.0.0.1:8000/api/run_template",
        json=body,
        timeout=15
    )
    response.raise_for_status()

    run_response_json = response.json()
    print("\nTemplate run started.")
    print(f"Run ID: {run_response_json.get('run_id')}")

    run_id = run_response_json.get('run_id')
    if run_id:
        results_response = requests.get(
            f"http://127.0.0.1:8000/api/results/{run_id}",
            timeout=15
        )
        results_response.raise_for_status()
        results = results_response.json()
        print("\nFetching results...")
        print(json.dumps(results, indent=2))

except requests.exceptions.RequestException as e:
    print("\nError during API request:")
    print(e)
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response body: {e.response.text}")
