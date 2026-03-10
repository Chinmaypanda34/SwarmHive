# run_template.py
import requests
import json
import sys

# Check if all required arguments are provided
if len(sys.argv) < 5:
    print("Usage: python run_template.py <spec_id> <template_path> <target_base> <consent>")
    sys.exit(1)

spec_id = sys.argv[1]
template_path = sys.argv[2]
target_base = sys.argv[3]
consent = sys.argv[4].lower() in ('true', '1', 't', 'y', 'yes')

try:
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
except FileNotFoundError:
    print(f"Error: Template file not found at {template_path}")
    sys.exit(1)

# Build the request body as a Python dictionary
body = {
    "spec_id": spec_id,
    "template": template_content,
    "target_base": target_base,
    "consent": consent
}

# Send the request
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/run_template",
        json=body,
        timeout=15
    )
    response.raise_for_status() # Raise an exception for bad status codes

    run_response_json = response.json()
    print("\nTemplate run started.")
    print(f"Run ID: {run_response_json.get('run_id')}")

    # Automatically fetch and display the results
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