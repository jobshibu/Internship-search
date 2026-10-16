from pipeline.db import get_connection, create_tables, upsert_listings
from pipeline.sources.simplify import parse, fetch
from pipeline.transform import make_listing_id, normalize_link

conn = get_connection()
create_tables(conn)
rows = parse(fetch())

for row in rows:
    row["link"] = normalize_link(row["url"])
    row["listing_id"] = make_listing_id(row["link"])

cur = conn.cursor()
cur.execute("SELECT count(*) FROM listings")
before = cur.fetchone()[0]
upsert_listings(conn, rows)
cur.execute("SELECT count(*) FROM listings")
total = cur.fetchone()[0]
new = total - before
cur.execute("INSERT INTO pipeline_runs (status) VALUES (%s) RETURNING run_id", ("success",))
run_id = cur.fetchone()[0]
print(f"run {run_id}: {new} new, {total} total")
cur.close()
conn.commit()
conn.close()