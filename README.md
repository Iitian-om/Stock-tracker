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

## Current tracked entities and live data

The default tracked entities are `RELIANCE.NS`, `TCS.NS`, and `INFY.NS` from NSE India, plus `AAPL` from the US market. They are classified as stocks. The default `.env.example` uses `PRICE_SOURCE=mock`, so displayed prices are generated demo values, not live market prices.

For provider-backed quotes, set `PRICE_SOURCE=yahoo`. The source uses Yahoo Finance's chart endpoint through the `requests` library. Examples include `RELIANCE.NS` (NSE), `RELIANCE.BO` (BSE), `AAPL` (US stock), `BTC-USD` (crypto), and `EURINR=X` (forex).

## Add a custom tracked entity

Use the dashboard's **Track a custom entity** form, or call the API directly:

```powershell
Invoke-RestMethod http://localhost:8000/entities -Method Post `
	-ContentType "application/json" `
	-Body '{"symbol":"BTC-USD","market":"Crypto market","entity_type":"crypto"}'
```

Supported types are `stock`, `etf`, `crypto`, `index`, `forex`, `commodity`, and `other`. View the configured list with `GET /entities`. The worker includes custom entities on its next fetch cycle.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/health` | DB status + worker freshness (used for SLA monitoring) |
| GET | `/prices` | Latest price of every symbol |
| GET | `/entities` | Tracked symbols with market and entity type |
| POST | `/entities` | Add or update a tracked symbol, market, and type |
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
