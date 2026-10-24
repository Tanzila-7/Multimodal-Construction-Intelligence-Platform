# BuildIntel — AI Construction Intelligence
React + FastAPI starter with safety image screening, crack screening, valuation, planning, assistant and weather advisory.

## Run backend
Python 3.10+:
cd backend
python -m venv .venv
Windows: .venv\\Scripts\\activate
macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
Copy .env.example to .env; optionally set OPENAI_API_KEY.
uvicorn app.main:app --reload

API docs: http://localhost:8000/docs

## Run frontend
Node 18+:
cd frontend
npm install
npm run dev
Open http://localhost:5173

Without an API key the application runs in demo mode. Configure OPENAI_API_KEY for multimodal image analysis and AI assistant answers.

IMPORTANT: AI image analysis is preliminary screening, not certified structural or safety inspection. Valuation is illustrative, not a market appraisal. Verify critical decisions with qualified professionals. Add authentication, persistent storage, rate limits and production CORS before deployment.
