# SmartERP Lite

Business ERP portfolio project: React + Flask + PostgreSQL.

## Features
- JWT login
- Employee CRUD
- Attendance
- Inventory with low-stock detection
- Sales endpoint with stock validation
- Dashboard KPIs
- PostgreSQL relational schema and foreign keys
- CSV sales report
- Dockerized PostgreSQL + Flask

## Run
`docker compose up --build`
Then in another terminal:
`docker compose exec backend python seed.py`
Then:
`cd frontend && npm install && npm run dev`

Demo:
`admin@smarterp.com` / `Admin@123`

## Interview knowledge
The backend uses PostgreSQL because ERP data is relational. Employees and attendance have a foreign-key relationship; sales and sale_items form another relationship. The sales endpoint uses a transaction and row locking so inventory cannot be oversold during concurrent requests.
