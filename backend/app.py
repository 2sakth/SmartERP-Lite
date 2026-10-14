import os, csv, io
from datetime import timedelta, date
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
app=Flask(__name__); CORS(app)
app.config["JWT_SECRET_KEY"]=os.getenv("JWT_SECRET_KEY","erp-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"]=timedelta(hours=8)
JWTManager(app)

def conn(): return psycopg2.connect(os.getenv("DATABASE_URL","postgresql://erp:erp@localhost:5432/smarterp"),cursor_factory=RealDictCursor)

SCHEMA="""
CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,name VARCHAR(120),email VARCHAR(160) UNIQUE,password TEXT,role VARCHAR(30) DEFAULT 'staff');
CREATE TABLE IF NOT EXISTS employees(id SERIAL PRIMARY KEY,name VARCHAR(120),email VARCHAR(160),department VARCHAR(80),position VARCHAR(80),salary NUMERIC(12,2),joined_date DATE DEFAULT CURRENT_DATE);
CREATE TABLE IF NOT EXISTS attendance(id SERIAL PRIMARY KEY,employee_id INT REFERENCES employees(id) ON DELETE CASCADE,date DATE DEFAULT CURRENT_DATE,status VARCHAR(30));
CREATE TABLE IF NOT EXISTS products(id SERIAL PRIMARY KEY,name VARCHAR(120),category VARCHAR(80),quantity INT DEFAULT 0,reorder_level INT DEFAULT 10,price NUMERIC(12,2));
CREATE TABLE IF NOT EXISTS sales(id SERIAL PRIMARY KEY,customer VARCHAR(120),total NUMERIC(12,2),sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sale_items(id SERIAL PRIMARY KEY,sale_id INT REFERENCES sales(id) ON DELETE CASCADE,product_id INT REFERENCES products(id),quantity INT,price NUMERIC(12,2));
"""
@app.before_request
def init():
    if request.path.startswith("/api/"):
        with conn() as c:
            with c.cursor() as cur: cur.execute(SCHEMA); c.commit()

@app.get("/api/health")
def health(): return jsonify({"status":"ok","service":"SmartERP Lite"})

@app.post("/api/auth/register")
def register():
    d=request.get_json() or {}
    if not all(d.get(x) for x in ("name","email","password")): return jsonify({"message":"Required fields missing"}),400
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s) RETURNING id",
                            (d["name"],d["email"].lower(),generate_password_hash(d["password"]),d.get("role","staff")))
                uid=cur.fetchone()["id"]; c.commit()
        return jsonify({"id":uid,"message":"Registered"}),201
    except Exception: return jsonify({"message":"Email already exists"}),409

@app.post("/api/auth/login")
def login():
    d=request.get_json() or {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s",(d.get("email","").lower(),)); u=cur.fetchone()
    if not u or not check_password_hash(u["password"],d.get("password","")): return jsonify({"message":"Invalid credentials"}),401
    return jsonify({"token":create_access_token(identity=str(u["id"])),"user":{"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"]}})

@app.get("/api/dashboard")
@jwt_required()
def dashboard():
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT COUNT(*) n FROM employees"); emp=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) n FROM products"); products=cur.fetchone()["n"]
            cur.execute("SELECT COALESCE(SUM(total),0) n FROM sales WHERE sale_date::date=CURRENT_DATE"); sales=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) n FROM attendance WHERE date=CURRENT_DATE AND status='Present'"); present=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) n FROM products WHERE quantity<=reorder_level"); low=cur.fetchone()["n"]
    return jsonify({"employees":emp,"products":products,"sales_today":float(sales),"present_today":present,"low_stock":low})

@app.get("/api/employees")
@jwt_required()
def employees():
    with conn() as c:
        with c.cursor() as cur: cur.execute("SELECT * FROM employees ORDER BY id DESC"); return jsonify(cur.fetchall())

@app.post("/api/employees")
@jwt_required()
def add_employee():
    d=request.get_json() or {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO employees(name,email,department,position,salary,joined_date) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *",
                        (d.get("name"),d.get("email"),d.get("department"),d.get("position"),d.get("salary",0),d.get("joined_date") or date.today()))
            row=cur.fetchone(); c.commit()
    return jsonify(row),201

@app.put("/api/employees/<int:eid>")
@jwt_required()
def edit_employee(eid):
    d=request.get_json() or {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("UPDATE employees SET name=%s,email=%s,department=%s,position=%s,salary=%s WHERE id=%s RETURNING *",
                        (d.get("name"),d.get("email"),d.get("department"),d.get("position"),d.get("salary",0),eid))
            row=cur.fetchone(); c.commit()
    return jsonify(row) if row else (jsonify({"message":"Not found"}),404)

@app.delete("/api/employees/<int:eid>")
@jwt_required()
def delete_employee(eid):
    with conn() as c:
        with c.cursor() as cur: cur.execute("DELETE FROM employees WHERE id=%s",(eid,)); c.commit()
    return jsonify({"message":"Employee deleted"})

@app.get("/api/products")
@jwt_required()
def products():
    with conn() as c:
        with c.cursor() as cur: cur.execute("SELECT * FROM products ORDER BY id DESC"); return jsonify(cur.fetchall())

@app.post("/api/products")
@jwt_required()
def add_product():
    d=request.get_json() or {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO products(name,category,quantity,reorder_level,price) VALUES(%s,%s,%s,%s,%s) RETURNING *",
                        (d.get("name"),d.get("category"),d.get("quantity",0),d.get("reorder_level",10),d.get("price",0)))
            row=cur.fetchone(); c.commit()
    return jsonify(row),201

@app.get("/api/attendance")
@jwt_required()
def attendance():
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("""SELECT a.*,e.name FROM attendance a JOIN employees e ON e.id=a.employee_id
                           WHERE a.date=CURRENT_DATE ORDER BY a.id DESC""")
            return jsonify(cur.fetchall())

@app.post("/api/attendance")
@jwt_required()
def mark_attendance():
    d=request.get_json() or {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO attendance(employee_id,date,status) VALUES(%s,%s,%s) RETURNING *",
                        (d["employee_id"],d.get("date") or date.today(),d.get("status","Present")))
            row=cur.fetchone(); c.commit()
    return jsonify(row),201

@app.post("/api/sales")
@jwt_required()
def sale():
    d=request.get_json() or {}; items=d.get("items",[])
    with conn() as c:
        with c.cursor() as cur:
            total=0
            for item in items:
                cur.execute("SELECT * FROM products WHERE id=%s FOR UPDATE",(item["product_id"],)); p=cur.fetchone()
                if not p or p["quantity"]<item["quantity"]: return jsonify({"message":f"Insufficient stock for product {item['product_id']}"}),400
                total += float(p["price"])*item["quantity"]
            cur.execute("INSERT INTO sales(customer,total) VALUES(%s,%s) RETURNING id",(d.get("customer","Walk-in"),total))
            sid=cur.fetchone()["id"]
            for item in items:
                cur.execute("SELECT price FROM products WHERE id=%s",(item["product_id"],)); price=cur.fetchone()["price"]
                cur.execute("INSERT INTO sale_items(sale_id,product_id,quantity,price) VALUES(%s,%s,%s,%s)",(sid,item["product_id"],item["quantity"],price))
                cur.execute("UPDATE products SET quantity=quantity-%s WHERE id=%s",(item["quantity"],item["product_id"]))
            c.commit()
    return jsonify({"message":"Sale recorded","sale_id":sid,"total":total}),201

@app.get("/api/reports/sales.csv")
@jwt_required()
def csv_report():
    with conn() as c:
        with c.cursor() as cur: cur.execute("SELECT id,customer,total,sale_date FROM sales ORDER BY sale_date DESC"); rows=cur.fetchall()
    out=io.StringIO(); w=csv.writer(out); w.writerow(["ID","Customer","Total","Date"])
    for r in rows: w.writerow([r["id"],r["customer"],r["total"],r["sale_date"]])
    mem=io.BytesIO(out.getvalue().encode()); return send_file(mem,download_name="sales_report.csv",as_attachment=True,mimetype="text/csv")

if __name__=="__main__": app.run(port=5002,debug=True)
