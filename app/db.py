import os
import psycopg
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    chat_id BIGINT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'idle',
    domain TEXT,
    years INTEGER,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT,
    provider_order_id TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    domain TEXT NOT NULL,
    years INTEGER NOT NULL,
    email TEXT NOT NULL,
    provider_order_id TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    final_price NUMERIC(12,2),
    currency TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

def connect():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required. Add a Render PostgreSQL database.")
    return psycopg.connect(url, row_factory=dict_row)

def init_db():
    with connect() as conn:
        conn.execute(SCHEMA)
        conn.commit()

def get_session(chat_id):
    with connect() as conn:
        return conn.execute("SELECT * FROM sessions WHERE chat_id=%s", (chat_id,)).fetchone()

def upsert_session(chat_id, **fields):
    current = get_session(chat_id)
    if current is None:
        with connect() as conn:
            conn.execute("INSERT INTO sessions(chat_id) VALUES(%s)", (chat_id,))
            conn.commit()
    if not fields:
        return
    fields["updated_at"] = None
    assignments=[]; values=[]
    for key, value in fields.items():
        if key == "updated_at":
            assignments.append("updated_at=NOW()")
        else:
            assignments.append(f"{key}=%s"); values.append(value)
    values.append(chat_id)
    with connect() as conn:
        conn.execute(f"UPDATE sessions SET {', '.join(assignments)} WHERE chat_id=%s", values)
        conn.commit()

def create_order(chat_id, domain, years, email, provider_order_id=None, final_price=None, currency=None, status="created"):
    with connect() as conn:
        row=conn.execute("""INSERT INTO orders(chat_id,domain,years,email,provider_order_id,final_price,currency,status)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (chat_id,domain,years,email,provider_order_id,final_price,currency,status)).fetchone()
        conn.commit()
        return row["id"]
