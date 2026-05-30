# FinRight AI — Personal Finance OS

Track income, expenses, goals, budgets and net worth — all in one place.

---

## Project Structure

```
finright-ai/
├── main.py                ← START HERE — runs the server
├── .env                   ← Your secret keys (never commit)
├── requirements.txt       ← Python packages
├── .gitignore
├── README.md
│
├── frontend/
│   └── index.html         ← The entire app (HTML + CSS + JS)
│
├── app/
│   ├── config.py          ← Loads settings from .env
│   ├── constants.py       ← Fixed values (categories, messages)
│   ├── database.py        ← Supabase connection helpers
│   ├── schema.py          ← Data validation models
│   ├── security.py        ← Auth, password, rate limiting
│   │
│   ├── routes/            ← One file per section
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── transactions.py
│   │   ├── goals.py
│   │   ├── budgets.py
│   │   ├── net_worth.py
│   │   ├── reports.py
│   │   ├── shopping.py
│   │   ├── activity_log.py
│   │   ├── income_sources.py
│   │   ├── taxonomy.py
│   │   ├── accounts.py
│   │   ├── profile.py
│   │   └── data_export.py
│   │
│   └── services/
│       └── analytics.py   ← All financial calculations
│
└── tests/
    └── test_transactions.py
```

---

## Setup

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Start server
python main.py
```

Open: http://localhost:8000/
API docs: http://localhost:8000/docs

---

## Frontend only (GitHub Pages)

Upload `frontend/index.html` as `index.html` to GitHub.
Live at: `https://jagrite07.github.io/finright-ai`
