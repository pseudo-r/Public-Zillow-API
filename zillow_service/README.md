# Zillow Service

Django REST API that wraps Zillow's undocumented endpoints.

## Quick Start

```bash
# Docker (recommended)
docker compose up --build

# API: http://localhost:8001
# Docs: http://localhost:8001/api/docs/
```

## Local Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check |
| `/api/v1/search/` | POST | Property search (sale, rent, sold) |
| `/api/v1/properties/{zpid}/` | GET | Property detail by ZPID |
| `/api/v1/properties/{zpid}/zestimate/` | GET | Zestimate + history |
| `/api/v1/properties/{zpid}/scores/` | GET | Walk/Transit/Bike scores |
| `/api/v1/properties/{zpid}/climate/` | GET | Climate risk scores |
| `/api/v1/autocomplete/?q={query}` | GET | Location suggestions |
| `/api/v1/ingest/property/` | POST | Ingest property by ZPID |
| `/api/schema/` | GET | OpenAPI schema |
| `/api/docs/` | GET | Swagger UI |

## Search Example

```bash
# Search for-sale homes in Seattle
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Seattle, WA",
    "type": "sale",
    "price_min": 400000,
    "price_max": 900000,
    "beds_min": 2
  }'

# Rental search in Austin
curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Austin, TX", "type": "rent", "rent_max": 2500}'

# Property detail
curl http://localhost:8001/api/v1/properties/2077091803/

# Zestimate + history
curl http://localhost:8001/api/v1/properties/2077091803/zestimate/

# Autocomplete
curl "http://localhost:8001/api/v1/autocomplete/?q=Seattle"

# Ingest a property
curl -X POST http://localhost:8001/api/v1/ingest/property/ \
  -H "Content-Type: application/json" \
  -d '{"zpid": 2077091803}'
```

## Zillow Client

`clients/zillow_client.py` provides `ZillowClient` with all major endpoints:

| Category | Methods |
|----------|---------|
| Search | `search_for_sale()`, `search_for_rent()`, `search_recently_sold()` |
| Autocomplete | `autocomplete()` |
| Property | `get_property_from_page()` |
| Zestimate | `get_zestimate()`, `get_zestimate_history()`, `get_rent_zestimate()` |
| Scores | `get_walk_bike_transit_scores()`, `get_climate_risk()` |
| Comps | `get_comparable_sales()`, `get_nearby_homes()`, `get_schools()` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (dev key) | Django secret key |
| `DEBUG` | `true` | Debug mode |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_DB` | `zillow_service` | Database name |
| `POSTGRES_USER` | `zillow` | Database user |
| `POSTGRES_PASSWORD` | `zillow` | Database password |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `ZILLOW_TIMEOUT` | `30` | Request timeout (seconds) |
| `ZILLOW_REQUEST_DELAY` | `1.5` | Delay between Zillow requests (seconds) |

## Notes

- Zillow blocks requests without browser-like headers — the client handles this automatically
- Set `ZILLOW_REQUEST_DELAY` ≥ 1.5s to avoid rate limiting
- Property detail extraction tries `__NEXT_DATA__` (Next.js) then `hdpApolloPreloadedData` (Apollo)
