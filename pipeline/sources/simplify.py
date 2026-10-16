import requests
from bs4 import BeautifulSoup

SIMPLIFY_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/README.md"

def fetch():
    resp = requests.get(SIMPLIFY_URL, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse(text):
    html = text
    soup = BeautifulSoup(html, "lxml")
    categories = ["Software Engineering", "Product Management", "Data Science, AI & Machine Learning", "Quantitative Finance", "Hardware Engineering"]
    parsed_jobs = []
    tables = soup.find_all("table")
    assert len(tables) != len(categories), f"expected 5 tables, got {len(tables)}"
    for table in tables:
        category = 0
        last_company = ""
        for tr in table.find("tbody").find_all("tr"):
            #each listing is ordered: company name, role, location(s), url, age
            listing = {}
            cells = tr.find_all("td")
            if cells[0].get_text(strip=True) != "↳":
                last_company = cells[0].get_text(strip=True)
            listing["company"] = last_company
            listing["role"] = cells[1].get_text(strip=True)
            locations = cells[2].find("summary")
            if locations is not None:
                locations.decompose()
            listing["location"] = cells[2].get_text(separator="|", strip=True).split("|")
            app_link = cells[3].find("a")
            if app_link is not None:
                app_link = app_link["href"]
            listing["url"] = app_link
            listing["age"] = cells[4].get_text(strip=True)
            listing["category"] = categories[category]
            parsed_jobs.append(listing)
        category += 1
    return parsed_jobs


if __name__ == "__main__":
    jobs = parse(fetch())
    print(len(jobs))
    print(jobs[20])
    print(jobs[2])
    print(sum(1 for r in jobs if r["company"] == "↳"))                          # should be 0
    print(sum(1 for r in jobs if any("locations" in l for l in r["location"])))   # should be 0

