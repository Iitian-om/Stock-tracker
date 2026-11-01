# Stock Price Tracker & Alert API

Cloud Computing mini project: FastAPI service + price worker, Dockerized, deployed on AWS.

## Run on your laptop (NO Docker needed)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
```
Open two terminals (activate the venv in both):
```bash
uvicorn app.main:app --reload        # terminal 1 -> http://localhost:8000  (API docs: /docs)
python -m app.worker                 # terminal 2 -> fetches prices every FETCH_INTERVAL seconds
```
Tip: set `FETCH_INTERVAL=10` in `.env` while testing.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/health` | DB status + worker freshness (used for SLA monitoring) |
| GET | `/prices` | Latest price of every symbol |
| GET | `/price/{symbol}` | Latest price of one symbol |
| GET | `/history/{symbol}?limit=100` | Price history |
| POST | `/alerts` | `{"symbol":"TCS.NS","condition":"above","threshold":4000}` |
| GET | `/alerts` | List alerts |
| DELETE | `/alerts/{id}` | Remove an alert |

## Run with Docker (on EC2 / Linux only)
```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f worker
```
Failure test for TTR: `docker kill <api-container>`; `restart: unless-stopped` brings it back. Time it.
