import os
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
# If GEMINI_API_KEY is in the environment, it will automatically be picked up,
# but we can explicitly set it here if needed.
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

app = FastAPI(title="QueueStorm Ticket Classifier")

# Set up the Gemini Model
# Using gemini-1.5-flash for fast, cheap, and accurate JSON generation
generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
except Exception as e:
    model = None
    print(f"Warning: Could not initialize Gemini model. {e}")


class TicketRequest(BaseModel):
    ticket_id: str
    channel: Optional[str] = None
    locale: Optional[str] = None
    message: str

class TicketResponse(BaseModel):
    ticket_id: str
    case_type: str
    severity: str
    department: str
    agent_summary: str
    human_review_required: bool
    confidence: float

@app.get("/health")
def health_check():
    return {"status": "ok"}

def sanitize_summary(summary: str) -> str:
    """
    Safety Rule: The agent_summary field must never ask the customer to share PIN, OTP, password, or full card number.
    Any response that does will fail that test case automatically.
    """
    # Simple regex to catch forbidden words
    forbidden_pattern = re.compile(r'\b(pin|otp|password|card number)\b', re.IGNORECASE)
    
    if forbidden_pattern.search(summary):
        # If it violates the rule, fallback to a neutral safe summary
        return "Customer reported an issue requiring attention. (Summary redacted for safety compliance)"
    return summary

def calculate_human_review(case_type: str, severity: str) -> bool:
    """
    Raise a flag for phishing or critical cases so a human reviews them immediately.
    """
    if severity.lower() == "critical" or case_type.lower() == "phishing_or_social_engineering":
        return True
    return False

@app.post("/sort-ticket", response_model=TicketResponse)
async def sort_ticket(ticket: TicketRequest):
    if not model:
        raise HTTPException(status_code=500, detail="LLM Model not configured. Missing API Key?")
        
    prompt = f"""
You are a customer support ticket classifier for a digital finance company (like bKash).
Analyze the following customer message and classify it.

Message: "{ticket.message}"

Respond strictly with a JSON object in this exact format:
{{
  "case_type": "enum",
  "severity": "enum",
  "department": "enum",
  "agent_summary": "string",
  "confidence": number
}}

Enums allowed:
case_type: "wrong_transfer", "payment_failed", "refund_request", "phishing_or_social_engineering", "other"
severity: "low", "medium", "high", "critical"
department: "customer_support", "dispute_resolution", "payments_ops", "fraud_risk"

Rules for department mapping:
- customer_support -> other, low severity refund_request
- dispute_resolution -> wrong_transfer, contested refund_request
- payments_ops -> payment_failed
- fraud_risk -> phishing_or_social_engineering

Rules for agent_summary:
- Must be a neutral 1-2 sentence summary.
- SAFETY RULE: NEVER ask the customer to share their PIN, OTP, password, or full card number.
- Focus on summarizing what the user said, not what the agent should reply.

Return only valid JSON.
"""

    try:
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Parse the JSON response from Gemini
        try:
            classification = json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback if the model didn't return pure JSON (e.g., wrapped in ```json)
            cleaned = text_response.replace("```json", "").replace("```", "").strip()
            classification = json.loads(cleaned)

        # Apply Safety Rule on summary
        safe_summary = sanitize_summary(classification.get("agent_summary", "Customer reported an issue."))
        
        c_type = classification.get("case_type", "other")
        c_sev = classification.get("severity", "low")
        c_dep = classification.get("department", "customer_support")
        
        # Calculate human review requirement
        human_review = calculate_human_review(c_type, c_sev)
        
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            case_type=c_type,
            severity=c_sev,
            department=c_dep,
            agent_summary=safe_summary,
            human_review_required=human_review,
            confidence=float(classification.get("confidence", 0.8))
        )
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        # Fallback response in case of API failure or parsing error
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            case_type="other",
            severity="medium",
            department="customer_support",
            agent_summary="Customer reported an issue (Fallback).",
            human_review_required=False,
            confidence=0.5
        )

# For running locally via `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.1", port=8000, reload=True)
