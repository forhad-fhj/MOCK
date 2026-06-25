# QueueStorm Warmup Service

This is the solution for the SUST CSE Carnival 2026 - Codex Community Hackathon (Mock Preliminary Round).
It is a small web service built with Python, FastAPI, and the Gemini API that classifies customer support tickets.

## Tech Stack
- Python 3.9+
- FastAPI
- Google Gemini API (for LLM-based text classification)
- Vercel (for deployment)

## Setup & Local Development

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd MOCK
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   Copy `.env.example` to `.env` and add your Google Gemini API key:
   ```bash
   cp .env.example .env
   ```
   Add: `GEMINI_API_KEY=your_actual_api_key_here`

4. Run the local development server:
   ```bash
   uvicorn main:app --reload
   ```
   The service will be available at `http://127.0.0.1:8000`.

## Endpoints
- `GET /health` - Health check.
- `POST /sort-ticket` - Analyzes a customer support ticket and returns a structured classification.

## Deployment to Vercel

This project includes a `vercel.json` configuration for easy deployment as a serverless function on Vercel.

1. Install the Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project root to link and deploy.
3. Add your `GEMINI_API_KEY` as an environment variable in the Vercel dashboard.
4. Run `vercel --prod` to deploy to production.
