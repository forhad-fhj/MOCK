import requests
import json

URL = "https://mock-iota-navy.vercel.app/sort-ticket"

test_cases = [
    {
        "ticket_id": "T-001",
        "message": "I sent 3000 to wrong number"
    },
    {
        "ticket_id": "T-002",
        "message": "Payment failed but balance deducted"
    },
    {
        "ticket_id": "T-003",
        "message": "Someone called asking my OTP, is that bKash?"
    },
    {
        "ticket_id": "T-004",
        "message": "Please refund my last transaction, I changed my mind"
    },
    {
        "ticket_id": "T-005",
        "message": "App crashed when I opened it"
    }
]

print(f"Testing against: {URL}\n")

for i, case in enumerate(test_cases, 1):
    print(f"--- Test Case {i} ---")
    print(f"Message: {case['message']}")
    
    payload = {
        "ticket_id": case["ticket_id"],
        "channel": "app",
        "locale": "en",
        "message": case["message"]
    }
    
    response = requests.post(URL, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Case Type: {result.get('case_type')}")
        print(f"Severity : {result.get('severity')}")
        print(f"Dept     : {result.get('department')}")
        print(f"Summary  : {result.get('agent_summary')}")
        print(f"Human Rev: {result.get('human_review_required')}")
    else:
        print(f"Error {response.status_code}: {response.text}")
    print("-" * 40 + "\n")
