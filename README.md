# AgentRaz

AI-powered agentic commerce platform for the **Razorpay AI Buildathon 2026 — Track 1**.

LLMs handle reasoning and orchestration; deterministic backend services handle business rules, authorization, payments, inventory, and financial actions.

## Architecture

```text
React Frontend → FastAPI Backend → PostgreSQL
                      ↓
              AI Agents + Policy Engine
                      ↓
               Razorpay Test Mode
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Configure .env (DATABASE_URL, GEMINI_API_KEY, RAZORPAY_*)
uvicorn app.main:app --reload --port 8000
```

### Database

```bash
psql $DATABASE_URL -f database/schema.sql
psql $DATABASE_URL -f database/seed.sql
psql $DATABASE_URL -f database/migrations/001_webhook_events.sql
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### Tests

```bash
cd backend && source venv/bin/activate
PYTHONPATH=. python -m pytest ../tests/test_commerce.py -v
```

### Synthetic Experiment

```bash
python experiments/generate_data.py --sessions 1000
python experiments/evaluate.py
```

> Results are labeled **Synthetic experiment** — not real-world outcomes.

## Key API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /buyer-agent/search` | NL → intent → recommendations |
| `POST /merchant-agent/offer` | Structured commerce offer |
| `POST /cart/calculate` | Deterministic cart totals |
| `POST /policy/check` | Authorization & spending limits |
| `POST /orders/` | Create order (policy-gated) |
| `POST /orders/{id}/pay` | Initiate Razorpay payment |
| `POST /payments/verify` | Server-side signature verify |
| `POST /webhooks/razorpay` | Idempotent webhook handler |
| `GET /audit/sessions/{id}` | Agent action audit trail |
| `GET /analytics/summary` | Revenue, conversion, AOV, upsell |

## Security Principles

- LLM never executes financial operations directly
- Prices always from PostgreSQL
- Policy engine gates all orders and payments
- Razorpay signatures verified server-side
- Webhook processing is idempotent
