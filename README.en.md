# AcessoHub

[Português (Brasil)](README.md) · [English](README.en.md)

A web application for managing members, subscription plans and access permissions. Built as a learning and portfolio project using Python, Flask and SQLite.

Administrators can register members, select a plan, renew access and review access and subscription records through a web interface with sidebar navigation. The application interface is in Brazilian Portuguese.

## Features

- Initial administrator setup, login and logout.
- Dashboard with member totals, membership status and recorded amounts.
- Member creation, editing, deletion and search by name, Brazilian CPF or ID.
- CPF, phone number and birth date validation, plus basic email checks.
- Filters for active, expired and suspended members.
- Monthly, quarterly, semiannual and annual plans at registration and renewal.
- Renewals that preserve the remaining subscription period.
- Member suspension and reactivation.
- Access checks with timestamps, results and reasons.
- Subscription history and monthly reports.
- Responsive page layouts.

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python and Flask |
| Database | SQLite |
| Interface | HTML, CSS and JavaScript |
| Templates | Jinja2 |
| Passwords | Werkzeug password hashing |

## Run locally

Requirement: Python 3.10 or later with pip. Open a terminal inside the project directory.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

These commands use the virtual environment interpreter directly; changing the PowerShell execution policy is unnecessary.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). On first launch, create an administrator with a username of at least three characters and a password of at least ten characters. Successful setup signs in the administrator and opens the dashboard.

The application creates `acesso.db` and the local `.session_key` automatically. Both are ignored by Git. Press `Ctrl + C` in the terminal to stop the server.

## Demo workflow

1. Create the administrator.
2. Register a member with fictional data and a valid CPF, selecting a plan.
3. Search for the member and check the expiration date.
4. Renew with another plan and review the subscription history under Mensalidades.
5. Suspend the member and run an access check to record the denial.
6. Reactivate the member and review access history and reports.

Use fictional data in demonstrations and screenshots.

## Demonstration plans

| Plan | Duration | Fictional price |
|---|---|---:|
| Monthly | 1 month | BRL 100.00 |
| Quarterly | 3 months | BRL 270.00 |
| Semiannual | 6 months | BRL 510.00 |
| Annual | 12 months | BRL 960.00 |

Plans are defined in the `PLANOS` dictionary in `app.py`. The backend determines the price from the selected plan. Registration and renewal record subscriptions; there is no card, Pix or payment gateway integration. Dashboard amounts represent recorded values, not bank-confirmed receipts.

Expiration dates use calendar months. If the original day does not exist in the target month, the last day of that month is used. For example, January 31, 2026 plus one month becomes February 28, 2026. Active subscriptions renew from their current expiration date; expired subscriptions renew from today. Access remains available on the expiration date, provided the member is not suspended.

## Code organization

| File / directory | Responsibility |
|---|---|
| `app.py` | Routes, authentication, validation, plans and access rules |
| `database.py` | SQLite connections, table creation and schema updates |
| `templates/` | HTML pages rendered with Jinja2 |
| `static/style.css` | Interface styling |
| `static/app.js` | Renewal dialog interaction |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes data, secrets and local files |
| `GITHUB.md` | Repository publishing instructions in Portuguese |

## Existing databases

Before updating an installation, stop the server and back up `acesso.db`. Preserve `.session_key` to retain the local signing key. Required tables and columns are created at startup.

Older members without a plan are labeled “Cadastro antigo” until renewed. Previous history is preserved. If an old database contains duplicate CPFs, migration keeps the records and skips creating the unique index until duplicates are resolved.

Deleting a member also deletes their subscription and access histories.

## Validation performed

Flask test client checks covered administrator creation and dashboard redirection, main page rendering, registration with a plan, server-selected pricing, renewal preserving existing validity, invalid plan rejection, calendar calculations and legacy database migration.

These checks do not replace browser interaction tests. The development verification scripts are not included in this package.

## Scope and limitations

This version is a local demonstration. It uses password hashing, form CSRF protection, parameterized SQL queries and HTTP-only session cookies. Login rate limiting, password recovery, multiple administrator roles and payment processing are not implemented.

Public deployment requires a security and personal data review, HTTPS, a WSGI server, backups and an appropriate environment-provided `SECRET_KEY`. Monetary amounts use SQLite `REAL` for simplicity; financial applications should use integer cents or another exact representation.

## Publishing to GitHub

See [GITHUB.md](GITHUB.md). The package excludes databases, credentials, virtual environments and session keys.
