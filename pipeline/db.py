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
