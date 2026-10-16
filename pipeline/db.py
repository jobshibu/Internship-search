import os
from dotenv import load_dotenv
import psycopg2


def get_connection():
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")

    conn = psycopg2.connect(db_url)
    return conn


def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    started_at timestamptz NOT NULL DEFAULT now(),
                    finished_at timestamptz,
                    rows_new int,
                    status text NOT NULL
    );
    CREATE TABLE IF NOT EXISTS listings (
                    listing_id text PRIMARY KEY,
                    company text NOT NULL,
                    role text NOT NULL,
                    link text NOT NULL,
                    locations text[] NOT NULL DEFAULT '{}',
                    category text,
                    age text,
                    first_seen_at timestamptz NOT NULL DEFAULT now(),
                    last_seen_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS run_issues (
                    issue_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    run_id integer REFERENCES pipeline_runs(run_id) NOT NULL,
                    severity text NOT NULL CHECK (severity IN ('HIGH','MEDIUM','LOW')),
                    code text NOT NULL,
                    detail text,
                    created_at timestamptz NOT NULL DEFAULT now()           
    );
    """)
    cur.close()

def upsert_listings(conn, rows):
    cur = conn.cursor()
    for row in rows:
        cur.execute(
            """INSERT INTO listings (listing_id, company, role, link, locations, category, age) VALUES (%(listing_id)s, %(company)s, %(role)s, %(link)s, %(location)s, %(category)s, %(age)s)
                ON CONFLICT (listing_id) DO UPDATE SET
                company = EXCLUDED.company,
                role = EXCLUDED.role,
                link = EXCLUDED.link,
                locations = EXCLUDED.locations,
                category = EXCLUDED.category,
                age = EXCLUDED.age,
                last_seen_at = now()
            """,
            row
        )
    cur.close()

def start_run(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO pipeline_runs (status) VALUES (%s) RETURNING run_id", ("running", ))
    run_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return run_id

def log_issue(conn, run_id, severity, code, detail):
    cur = conn.cursor()
    cur.execute ("INSERT INTO run_issues (run_id, severity, code, detail) VALUES (%s, %s, %s, %s)",
                 (run_id, severity, code, detail, ))
    cur.close()

def finish_run(conn, run_id, status, rows_new):
    cur = conn.cursor()
    cur.execute("UPDATE pipeline_runs SET status = %s, rows_new = %s, finished_at = now() WHERE run_id = %s",
                (status, rows_new, run_id, ))
    cur.close()

