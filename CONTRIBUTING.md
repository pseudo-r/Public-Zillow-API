# Contributing to Public-Zillow-API

Thank you for your interest in contributing! This project documents Zillow's undocumented internal API and provides a Django-based service for consuming it.

## Ways to Contribute

### 📖 Documentation
- Add or correct endpoint URLs
- Document new GraphQL operations
- Improve or add curl examples
- Add response schema examples to `docs/response_schemas.md`
- Fix errors, typos, or outdated information

### 🐛 Report a Bug
Open an issue using the **🐛 Bug Report** template. Please include:
- The endpoint URL you used
- What you expected
- What you actually received (status code, response snippet)

### 🆕 Report a Missing Endpoint
Open an issue using the **🔍 Missing Endpoint** template. If you've found a Zillow API endpoint not documented here, we want to know!

### 💻 Code (zillow_service)
Fix bugs or add features to the Django service. Please include tests for any code changes.

---

## Development Setup

### 🐳 Docker (recommended — one command)

```bash
git clone https://github.com/pseudo-r/Public-Zillow-API.git
cd Public-Zillow-API

# Copy env file
cp .env.example zillow_service/.env

# Start PostgreSQL, Redis, Django + Celery
docker compose up
```

API at **http://localhost:8001** · Swagger UI at **http://localhost:8001/api/schema/swagger-ui/**

---

### 🐍 Local (without Docker)

Prerequisites: Python 3.12+, PostgreSQL 14+, Redis 6+.

```bash
cd zillow_service
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Copy and edit env
cp ../.env.example .env
# Set DATABASE_URL and CELERY_BROKER_URL to your local values

python manage.py migrate
python manage.py runserver
```

---

## Pull Request Guidelines

1. **Branch off `main`** — this is the default branch
2. **One concern per PR** — keep changes focused
3. **Write clear commit messages** — reference the endpoint or file you changed
4. **Add tests** for any `zillow_service` code changes
5. **Update docs** if you change endpoints or add new features

### Commit message format

```
type: short description

- Bullet detail if needed
```

Types: `docs`, `feat`, `fix`, `test`, `chore`

---

## Documentation Style Guide

### Endpoint format

Each endpoint should include:
- Full URL
- Method (GET / POST / PUT)
- Verification status (VERIFIED / PARTIALLY VERIFIED / UNVERIFIED)
- Required headers
- Required and optional params
- Example request (curl)
- Example response (trimmed real JSON)
- Notes

### Curl examples

- Use `https://` always
- Add a `# comment` above each curl example
- Use real working values in examples (not `{placeholder}` where avoidable)
- Include required `User-Agent` header

### File locations

| What | Where |
|------|-------|
| Main endpoint reference | `README.md` |
| Category-specific docs | `docs/endpoints/{category}.md` |
| Response JSON examples | `docs/response_schemas.md` |
| Change history | `CHANGELOG.md` |

---

## Code of Conduct

Be kind and respectful. This is a community resource — everyone is welcome.

---

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) as this project.
