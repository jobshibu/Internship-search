from pipeline.db import get_connection, create_tables, upsert_listings, start_run, log_issue, finish_run
from pipeline.sources.simplify import parse, fetch
from pipeline.transform import make_listing_id, normalize_link

MIN_ROWS = 500

conn = get_connection()
create_tables(conn)
run_id = start_run(conn)
try:
    rows = parse(fetch())
    if len(rows) < MIN_ROWS:
        log_issue(conn, run_id, "HIGH", "too_few_rows", f"parsed {len(rows)} rows, expected >= {MIN_ROWS}")
        finish_run(conn, run_id, 'degraded', 0)
    else:
        valid_rows = []
        for row in rows:
            if(row["url"] is None):
                log_issue(conn, run_id, "LOW", "missing_link", f"company: {row['company']} role: {row['role']}")
                continue
            row["link"]= normalize_link(row["url"])
            row["listing_id"] = make_listing_id(row["link"])
            valid_rows.append(row)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM listings")
        before = cur.fetchone()[0]
        upsert_listings(conn, valid_rows)
        cur.execute("SELECT count(*) FROM listings")
        total = cur.fetchone()[0]
        new = total - before
        finish_run(conn, run_id, "success", new)
        print(f"run {run_id}: {new} new, {total} total")
        cur.close()
    conn.commit()
except Exception as e: 
    conn.rollback()
    log_issue(conn, run_id, "HIGH", "exception", str(e))
    finish_run(conn, run_id, "failed", None)
    conn.commit()
    raise
finally:
    conn.close()