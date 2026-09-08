# Whimsy — Full-Stack E-Commerce Store

A production-oriented Flask + SQLAlchemy toy-store application designed for local development, Supabase PostgreSQL, Supabase Storage and Render's free web service.

## What is included

- Customer storefront with responsive premium/playful design
- Exact supplied Whimsy logo stored as the brand asset
- Product search, category filters, price filters, sorting and pagination
- Product detail pages, stock states and related products
- Secure customer registration/login with Werkzeug password hashing
- Customer account/profile and order history
- Session cart with server-side stock validation
- Checkout that recalculates prices and stock on the server
- PostgreSQL-safe row locking with `FOR UPDATE` for checkout where supported
- Order snapshots for product names/prices
- Stock deduction/restoration protected by `stock_deducted`
- Admin role and protected `/admin/*` routes
- Admin dashboard, products, categories, orders, customers and messages
- Admin order deletion with exact-once stock restoration
- Contact/message system
- CSRF protection with Flask-WTF
- Secure session cookie settings
- Supabase Storage upload integration for product images
- Flask-Migrate database migrations
- Gunicorn + Render configuration
- Automated tests for the critical flows
- Friendly 403/404/500 pages

## Project structure

```text
whimsy/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── shop.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   ├── admin.py
│   │   └── messages.py
│   ├── utils/
│   │   ├── helpers.py
│   │   └── storage.py
│   ├── templates/
│   └── static/
├── migrations/
├── tests/
├── config.py
├── create_admin.py
├── run.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
└── README.md
```

## 1. Local installation

Python 3.11+ is recommended.

```bash
git clone <your-repository-url>
cd whimsy
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and change the values.

For quick local development you may leave `DATABASE_URL` unset; the app falls back to a local SQLite database. **SQLite is only a local-development convenience and is not the production database.**

Run migrations:

```bash
flask --app run:app db upgrade
```

Start locally:

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

## 2. Environment variables

```env
SECRET_KEY=change-me
DATABASE_URL=your-supabase-postgresql-url
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_BUCKET=product-images
SESSION_COOKIE_SECURE=0
SHIPPING_FEE=200
LOW_STOCK_DEFAULT=5
ITEMS_PER_PAGE=12
ADMIN_ITEMS_PER_PAGE=20
```

- `SECRET_KEY`: Flask session/CSRF signing secret. Use a long random value in production.
- `DATABASE_URL`: Supabase PostgreSQL connection string. Never commit it.
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_KEY`: Supabase API key used by the server where appropriate.
- `SUPABASE_SERVICE_ROLE_KEY`: preferred server-only key for product-image uploads. **Never put this in frontend JavaScript or expose it to customers.**
- `SUPABASE_BUCKET`: Storage bucket name.
- `SESSION_COOKIE_SECURE`: use `1` on HTTPS production; keep `0` for plain local HTTP.
- `SHIPPING_FEE`: current flat delivery fee in PKR.

## 3. Supabase PostgreSQL setup

1. Create a Supabase project.
2. Open the project's database connection settings.
3. Copy a PostgreSQL connection string suitable for your deployment.
4. Put it in `DATABASE_URL`.
5. Do not commit the connection string.
6. Run `flask --app run:app db upgrade`.

For Render, prefer a connection string that works reliably from external hosting. If your provider offers both pooled and direct connections, use the provider's documented production option for your region/runtime.

## 4. Supabase Storage setup

Create a bucket named `product-images` (or choose another name and set `SUPABASE_BUCKET`). Make the bucket public if you want product image URLs to be directly viewable by customers.

For server-side uploads, configure `SUPABASE_SERVICE_ROLE_KEY` on Render. The key stays server-side; it is never rendered into templates.

If you do not want to use uploads yet, the admin product form also accepts a persistent image URL. Do not use Render's local filesystem as permanent product storage.

## 5. Create the first admin

After the database exists:

```bash
python create_admin.py
```

The script interactively asks for the admin name, email and password. The password is hashed before it is stored.

Then visit `/login` and sign in. Admins can open `/admin`.

## 6. Database migrations

Initial migration is included in `migrations/versions/`.

For future model changes:

```bash
flask --app run:app db migrate -m "describe the change"
flask --app run:app db upgrade
```

Never use destructive table resets in production.

## 7. Render deployment

The included `render.yaml` is configured for a free Python web service.

Build command:

```bash
pip install -r requirements.txt && flask --app run:app db upgrade
```

Start command:

```bash
gunicorn run:app
```

Set these Render environment variables:

- `SECRET_KEY` — generate a strong secret
- `DATABASE_URL` — Supabase PostgreSQL URL
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_BUCKET=product-images`
- `SESSION_COOKIE_SECURE=1`
- `SHIPPING_FEE=200`

After deployment, run `python create_admin.py` against the production database if you have shell access, or use the same script from a controlled environment pointing at the production `DATABASE_URL`.

### Important Render note

Render's local filesystem is ephemeral. This project therefore does not treat `app/static/uploads` as permanent product storage. Product images should live in Supabase Storage or another persistent object store.

## 8. Testing

Run:

```bash
pytest -q
```

The tests cover registration, duplicate registration, invalid login, logout, admin authorization, cart quantity limits, checkout, stock deduction, customer order access, CSRF rejection and contact messages.

The test configuration uses an isolated in-memory SQLite database only for test execution. Production uses PostgreSQL via `DATABASE_URL`.

## 9. Security notes

- Passwords are stored as Werkzeug hashes, never plaintext.
- Every state-changing form is CSRF-protected.
- Admin authorization is checked on every admin endpoint.
- Customer order routes verify ownership.
- Browser prices are never trusted during checkout.
- Product stock is re-read from the database before checkout.
- PostgreSQL row locking is requested during stock reservation.
- Order item names/prices are snapshotted.
- Stock restoration is controlled by `stock_deducted` so cancellation/deletion cannot restore the same reservation twice.
- Product deletion is blocked when historical order items reference the product; deactivate the product instead.
- Production secrets are environment variables.
- Production error responses do not expose Python stack traces.

## 10. Stock lifecycle

At checkout, each product is re-read and locked where the database supports row locks. If requested quantity exceeds current stock, the order is rejected. Prices are also recalculated from the database.

On successful order creation:

```text
stock = stock - purchased_quantity
stock_deducted = True
```

When an order is cancelled or deleted while `stock_deducted=True`:

```text
stock = stock + purchased_quantity
stock_deducted = False
```

This makes restoration idempotent for the order lifecycle implemented here.

## 11. Important operational limitation

The app is production-oriented, but no generated software should be described as universally bug-free. Before taking real payments or large order volume, connect your real Supabase/Render environment and perform a staging checkout, image upload, migration and concurrent-stock test.

The current checkout is intentionally cash/manual-payment friendly: it creates an order and manages inventory, but it does not pretend to have a payment gateway. A payment provider can be added later without changing the core order snapshot/stock design.
