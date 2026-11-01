# Hooklab 🪝

**A local-first webhook inspection workbench.** Catch incoming webhook requests, inspect headers and payloads, and replay captured events into another local inbox — without digging through application logs.

> Status: early MVP (0.1.0). Built for local development and testing, not yet hardened for public multi-tenant production use.

## Features
- Create multiple named webhook endpoints with cryptographically random capture tokens.
- Capture GET, POST, PUT, PATCH, DELETE, OPTIONS, and HEAD requests.
- Preserve method, path, query, headers, raw body, content type, source address, and timestamp.
- Inspect events in a responsive browser dashboard.
- Replay events into another Hooklab inbox, preserving binary payload bytes.
- SQLite persistence, Docker volume, configurable payload limit, and OpenAPI docs.

## Quick start
Requires Python 3.10+.

    python -m venv .venv
    # Windows: .venv\\Scripts\\activate
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000, create an endpoint, and send a test event:

    curl -X POST http://127.0.0.1:8000/hook/YOUR_TOKEN/orders -H 'Content-Type: application/json' -H 'X-Event-Type: order.created' -d '{"order_id":"ord_123","total":499}'

## Docker
    docker compose up --build

Dashboard: http://localhost:8000 · API docs: http://localhost:8000/docs

## API
| Method | Path | Purpose |
|---|---|---|
| GET | /health | Health check |
| POST | /api/endpoints | Create inbox: {"name":"Stripe"} |
| GET | /api/endpoints | List inboxes |
| DELETE | /api/endpoints/{id} | Delete inbox and events |
| GET | /api/requests | List events; optional endpoint_id and limit |
| GET | /api/requests/{id} | Inspect event, including raw-body base64 |
| POST | /api/requests/{id}/replay | Copy to another inbox |
| ANY | /hook/{token}/{path} | Capture webhook |

## Configuration
- HOOKLAB_DB: SQLite file path (default: ./data/hooklab.db).
- HOOKLAB_MAX_BODY_BYTES: maximum request body (default: 1 MiB).

## Tests
    pip install -r requirements.txt
    pytest -q

## Security and scope
Treat capture URLs as secrets. Captured headers and bodies may contain credentials or personal data: keep the database private and never commit it. Do not expose this development instance publicly without authentication, rate limiting, retention controls, TLS, and deployment hardening. The dashboard is for a trusted local environment; multi-user auth and tenant isolation are not implemented. Replay is intentionally restricted to copying between local Hooklab inboxes; it does not make arbitrary outbound HTTP requests, avoiding an SSRF footgun in the MVP.

## Roadmap
- [ ] Search, filters, and retention policies
- [ ] Stripe, GitHub, and Razorpay signature verification
- [ ] CLI and cURL/JSON fixture export
- [ ] Hosted relay, team workspaces, auth, quotas, and audit log

## Contributing
Issues and pull requests welcome. Please include a failing test for bug fixes and new behavior.

## License
MIT — see LICENSE.
