# Neo Project

Backend API for **Neo**, a dog-adoption platform. Kennels (shelters) sign in with JWT and manage adoptable dogs; visitors browse breeds, dogs, blog, shop, and contact flows. The API also supports **breed matching** and **dog matching** from questionnaire-style payloads.

## Stack

| Piece | Technology |
|--------|------------|
| Framework | Django 4, Django REST Framework |
| Auth | SimpleJWT (Bearer access + refresh); custom user model `adoption_kennel.Kennel` |
| API layout | Central [`routers.py`](routers.py) under `/api/` |
| Admin | Django admin at **`/dogs/`** (see [`neoProject/urls.py`](neoProject/urls.py)) |
| DB | SQLite for local dev; PostgreSQL in production via `DATABASE_URL` |
| Static | WhiteNoise; `collectstatic` for deployment |

## Prerequisites

- Python 3.11 (matches [Render](https://render.com/) config in [`render.yaml`](render.yaml))
- For PostgreSQL locally: a running Postgres instance and `DATABASE_URL` (optional; SQLite is the default without it)

## Local setup

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set a secret key (required by [`neoProject/settings.py`](neoProject/settings.py)):

   ```bash
   export SECRET_KEY="your-dev-secret-key"
   ```

   For convenience you can add a local-only `env.py` at the repo root (it is [gitignored](.gitignore)) and define `SECRET_KEY` there; `settings.py` imports `env` when present.

3. Apply migrations and create a superuser if you need admin access:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Run the development server:

   ```bash
   python manage.py runserver
   ```

With `ENV` unset or not `PROD`, and without `DATABASE_URL`, the project uses **`db.sqlite3`** in the project root.

### Optional: PostgreSQL

Set `DATABASE_URL` (or run with `ENV=PROD` and Postgres env vars as in settings) to use PostgreSQL instead of SQLite.

### Breed catalog import

After migrations, you can load or update breeds from the bundled CSV (same command used on deploy in `render.yaml`):

```bash
python manage.py import_dogdb_csv DogDB.csv --update
```

## Tests

```bash
python manage.py test
```

## Deployment

- **[`render.yaml`](render.yaml)** — web service + managed Postgres: build runs `migrate`, `collectstatic`, and the DogDB import; start uses Gunicorn.
- **[`Procfile`](Procfile)** — `gunicorn neoProject.wsgi:application` with extended timeouts.

Set production secrets (`SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, etc.) in your host’s environment; do not commit them.

## Documentation in this repo

| Doc | Contents |
|-----|----------|
| [`NEO_PROJECT.md`](NEO_PROJECT.md) | Architecture, product areas, matching behavior, API intent |
| [`API_LIST.md`](API_LIST.md) | API surface / endpoints |
| [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md) | Deploy verification steps |

## License

Add a `LICENSE` file if you want this repository to be open source under explicit terms.
