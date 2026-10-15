import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

db_url = os.getenv("DATABASE_URL")

conn = psycopg2.connect(db_url)

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS pipeline_runs (
                 run_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                 started_at timestamptz NOT NULL DEFAULT now(),
                 status text NOT NULL
);
""")

cur.execute("INSERT INTO pipeline_runs (status) VALUES (%s) RETURNING run_id;", ("success",))
print(cur.fetchone()[0])

conn.commit()
cur.close()
conn.close()
