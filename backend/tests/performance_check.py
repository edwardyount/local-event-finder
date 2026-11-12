"""NFR-01: browse/search/filter over 500+ events. Run from backend/: python tests/performance_check.py"""
import os, platform, subprocess, sys, tempfile, time, statistics

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
os.environ["EVENTS_DB"] = os.path.join(TMP, "perf.db")
os.environ["SECRET_KEY_FILE"] = os.path.join(TMP, "k")
sys.path.insert(0, BACKEND)
subprocess.run([sys.executable, "seed.py", "--bulk"], cwd=BACKEND, env=os.environ, check=True, capture_output=True)
from app import app  # noqa: E402
import sqlite3
n = sqlite3.connect(os.environ["EVENTS_DB"]).execute("select count(*) from events").fetchone()[0]
c = app.test_client()
queries = {"browse all": "/api/events", "search 'music'": "/api/events?q=music", "no-match search": "/api/events?q=zzzznomatch",
           "category filter": "/api/events?categories=1,2", "date range": "/api/events?startDate=2026-11-01&endDate=2027-12-31"}
print(f"Machine: {platform.platform()} | Python {platform.python_version()} | events: {n}")
worst = 0
for name, url in queries.items():
    t = []
    for _ in range(5):
        s = time.perf_counter(); r = c.get(url); t.append(time.perf_counter() - s)
        assert r.status_code == 200
    worst = max(worst, max(t))
    print(f"{name:18} avg {statistics.mean(t)*1000:6.1f} ms   max {max(t)*1000:6.1f} ms")
print("PASS (all under 2 s)" if worst < 2 else "FAIL (over 2 s)")
