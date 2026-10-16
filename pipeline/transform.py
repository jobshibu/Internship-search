import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

def normalize_link(url):
    parts = urlsplit(url)
    parse_query = parse_qsl(parts.query)
    approved_query = []
    for query in parse_query:
        if not (query[0].startswith("utm_") or query[0] == "ref"):
            approved_query.append(query)
    query = urlencode(sorted(approved_query))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))

def make_listing_id(normalized_url):
    return hashlib.sha1(normalized_url.encode()).hexdigest()
