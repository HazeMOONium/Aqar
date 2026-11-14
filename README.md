# Aqar — Real Estate Client Application (Final Milestone)

A Streamlit **web application** (GUI → bonus) that connects to the **Aqar database hosted on a
remote MySQL server** (`sql.freedb.tech:3306` — not localhost). All connection details are read
from `.env`.

## Deliverables

| File | Purpose |
|---|---|
| `app.py` | The web application (source code = executable via Streamlit) |
| `db.py` | Remote MySQL connection helper (reads `.env`) |
| `setup_users_reviews.py` | Creates the `users` + `reviews` tables on the remote server (idempotent) |
| `aqar_database_dump.sql` | **Latest full dump** of the remote database (all 5 tables, schema + data) |
| `.env` | DB configuration |
| `dump.sql` | Original dataset dump |

## Requirements

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the browser at `http://localhost:8501`.

> `.env` must contain:
> ```ini
> DB_HOST=sql.freedb.tech
> DB_PORT=3306
> DB_DATABASE=freedb_yiPKYe9K
> DB_USERNAME=u_hRmt84
> DB_PASSWORD=...
> ```

## Features → Pages

| # | Required feature | Page in the app |
|---|---|---|
| 1 | Register a user | 👤 Register |
| 2 | Add a user review on a project | 💬 Project Reviews (login required) |
| 3 | View existing reviews of a project | 💬 Project Reviews |
| 4 | Top 10 projects: highest resale inventory / resale amount / gain over market, by property type | 🏆 Top 10 Projects |
| 5 | Location of a development + avg price/sqm & listings per unit type | 📍 Development Location |
| 6 | All properties in an area + avg price/sqm per unit type | 🏘️ Properties by Area |
| 7 | Properties in an area within a price range + amenities | 🔍 Area + Price + Amenities |
| 8 | Top 5 developers by resale listings (avg price/sqm, avg down payment, gain) | 🏗️ Top 5 Developers |
| 9 | All properties by area, property type, contract year | 📋 Browse Properties |
| 10 | Avg installment, avg down payment, #properties, avg discount, avg contract age, avg market price by area & project | 💰 Market Analysis |

### Schema interpretation notes

- **Resale listings** — every listing in `PROPERTY` is a secondary-market (resale) listing;
  resale inventory = `COUNT(*)`, resale amount = `SUM(Area × Price_per_m2)`.
- **Down payment** — the `Down_payment` column is empty in the dataset, so the
  "required down payment" metric uses `Cash_required_now`.
- **Gain / discount over market** — the `Gain_over_current` column (EGP gain vs current market value).
- **users / reviews** — not part of the original dump, created by `setup_users_reviews.py`
  (FKs to `DEVELOPMENT_PROJECT(Name)`).

## Demo account

`demo@aqar.com` / `password123` (has 3 sample reviews), or register a new account from the app.
