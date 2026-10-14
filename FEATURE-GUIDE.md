# SmartERP Lite — Feature Guide

## Included working features
- JWT registration/login
- Employee create/list/update/delete APIs (UI currently provides add/list)
- Attendance marking and listing
- Product create/list and low-stock indication
- Dashboard KPIs: employees, products, today's sales, attendance, low stock
- Sales API validates stock, records sale items and decrements stock in a DB transaction
- PostgreSQL relational schema with foreign keys
- CSV sales report download endpoint
- Docker Compose and seed data

## Run
1. Install Docker Desktop and Node.js.
2. In this folder: `docker compose up --build`
3. In another terminal: `docker compose exec backend python seed.py`
4. `cd frontend && npm install && npm run dev`
5. Demo login: `admin@smarterp.com` / `Admin@123`

## Honest scope
This is a portfolio MVP, not a payroll/accounting system suitable for real company use. Payroll, PDF reports, detailed role permissions, editing/deleting products in the UI, automated tests and audit logs are future enhancements; don't claim those as implemented.
