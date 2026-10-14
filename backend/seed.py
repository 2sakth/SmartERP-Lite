from app import conn
from werkzeug.security import generate_password_hash
from datetime import date
with conn() as c:
    with c.cursor() as cur:
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s) ON CONFLICT(email) DO NOTHING",
                    ("Admin","admin@smarterp.com",generate_password_hash("Admin@123"),"admin"))
        cur.execute("INSERT INTO employees(name,email,department,position,salary) VALUES(%s,%s,%s,%s,%s)",("Anitha","anitha@demo.com","HR","HR Executive",32000))
        cur.execute("INSERT INTO employees(name,email,department,position,salary) VALUES(%s,%s,%s,%s,%s)",("Bala","bala@demo.com","IT","Developer",42000))
        cur.execute("INSERT INTO products(name,category,quantity,reorder_level,price) VALUES(%s,%s,%s,%s,%s)",("Wireless Mouse","Accessories",42,10,699))
        cur.execute("INSERT INTO products(name,category,quantity,reorder_level,price) VALUES(%s,%s,%s,%s,%s)",("Keyboard","Accessories",25,8,1199))
        c.commit()
print("Seed complete: admin@smarterp.com / Admin@123")
