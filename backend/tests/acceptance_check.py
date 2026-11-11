"""Acceptance checks against the API (FR-01 to FR-10, NFR-06, NFR-07).

Run from backend/:   python tests/acceptance_check.py
Uses a throwaway database and key.
"""
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
DB = os.path.join(TMP, "acceptance.db")
os.environ["EVENTS_DB"] = DB
os.environ["SECRET_KEY_FILE"] = os.path.join(TMP, "secret_key")
os.environ.pop("SECRET_KEY", None)
sys.path.insert(0, BACKEND)
subprocess.run([sys.executable, "seed.py"], cwd=BACKEND, env=os.environ, check=True, capture_output=True)

from app import app  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"   -> {detail}"))


def call(c, method, url, **body):
    token = c.get("/api/csrf-token").get_json()["csrfToken"]
    kw = {"headers": {"X-CSRFToken": token}}
    if method != "get":
        kw["json"] = body
    r = getattr(c, method)(url, **kw)
    data = r.get_json(silent=True)
    if isinstance(data, dict):
        if "events" in data:
            data = data["events"]
        elif "event" in data and "created" not in data:
            data = data["event"]
    return r.status_code, data


def login(c, email, pw="password123"):
    return call(c, "post", "/api/auth/login", email=email, password=pw)


def sql(q, *a):
    conn = sqlite3.connect(DB)
    try:
        return conn.execute(q, a).fetchall()
    finally:
        conn.close()


alice, bob, anon = app.test_client(), app.test_client(), app.test_client()
login(alice, "alice@example.com")
login(bob, "bob@example.com")

# FR-01 Registration / login
c = app.test_client()
s, _ = call(c, "post", "/api/auth/register", displayName="Cara", email="Cara@Example.com ", password="longenough1")
check("FR-01 register ok", s in (200, 201), s)
s, _ = call(app.test_client(), "post", "/api/auth/register", displayName="Dup", email="cara@example.com", password="longenough1")
check("FR-01 duplicate email rejected (409)", s == 409, s)
s, _ = call(app.test_client(), "post", "/api/auth/register", displayName="X", email="bad", password="x")
check("FR-01 invalid input rejected (400)", s == 400, s)
s, r1 = login(app.test_client(), "alice@example.com", "wrongpass")
s2, r2 = login(app.test_client(), "nobody@example.com", "wrongpass")
check("FR-01 wrong password / unknown email give same generic error", s == s2 == 401 and r1 == r2, (r1, r2))
check("FR-01 password stored hashed", all(p[0] != "password123" and len(p[0]) > 40 for p in sql("select password_hash from users")))
s, me = call(alice, "get", "/api/auth/me")
check("FR-01 session identifies user", s == 200)
s, _ = call(anon, "get", "/api/auth/me")
check("FR-01 anonymous /me returns no user", s == 200 and _["user"] is None, _)

# FR-02 Browse / search / filter
s, ev = call(anon, "get", "/api/events")
check("FR-02 anonymous can browse", s == 200 and len(ev) > 0)
check("FR-02 only upcoming events", all(e["title"] != "TEST Started Event" for e in ev))
check("FR-02 sorted soonest first", [(e["date"], e["startTime"]) for e in ev] == sorted((e["date"], e["startTime"]) for e in ev))
s, r = call(anon, "get", "/api/events?q=zzzznomatch")
check("FR-02 no match -> empty list (not error)", s == 200 and r == [])
s, r = call(anon, "get", "/api/events?q=%25")
check("FR-02 '%' searched literally", s == 200 and r == [])
cid = ev[0]["categoryId"]; cname = ev[0]["category"]
s, r = call(anon, "get", "/api/events", )
s, r = call(anon, "get", f"/api/events?categories={cname}")
check("FR-02 category filter", s == 200 and r and all(e["category"] == cname for e in r))
s, r = call(anon, "get", f"/api/events?startDate={ev[-1]['date']}&endDate={ev[-1]['date']}")
check("FR-02 date range filter", s == 200 and r and all(e["date"] == ev[-1]["date"] for e in r))
s, r = call(anon, "get", "/api/events?startDate=2030-02-01&endDate=2030-01-01")
check("FR-02 reversed dates -> 400", s == 400, s)
check("FR-02 category image is a local file", all(e["categoryImage"].startswith("/images/categories/") for e in ev))

# FR-03 Event details
e0 = ev[0]
s, d = call(anon, "get", f"/api/events/{e0['id']}")
need = {"title", "description", "location", "date", "startTime", "endTime", "creator", "capacity", "activeRSVPCount", "seatsLeft", "category"}
check("FR-03 detail has all fields", s == 200 and need <= set(d), need - set(d or {}))
s, _ = call(anon, "get", "/api/events/99999")
check("FR-03 unknown event -> 404", s == 404, s)

# FR-04 Favorites
fid = e0["id"]
s, _ = call(anon, "post", f"/api/favorites/{fid}")
check("FR-04 favorites need login (401)", s == 401, s)
call(alice, "post", f"/api/favorites/{fid}")
s, _ = call(alice, "post", f"/api/favorites/{fid}")
check("FR-04 favoriting twice is harmless", s == 200, s)
check("FR-04 no duplicate rows", sql("select count(*) from favorites where event_id=?", fid)[0][0] == 1)
s, f = call(alice, "get", "/api/favorites")
check("FR-04 list favorites", s == 200 and any(x["id"] == fid for x in f))
s, f = call(bob, "get", "/api/favorites")
check("FR-04 favorites are per user", not any(x["id"] == fid for x in f))
call(alice, "delete", f"/api/favorites/{fid}")
s, f = call(alice, "get", "/api/favorites")
check("FR-04 unfavorite", not any(x["id"] == fid for x in f))
s, _ = call(alice, "post", "/api/favorites/99999")
check("FR-04 favorite unknown event -> 404", s == 404, s)

# FR-05/06/07 RSVP
free = sql("select event_id from events where title='TEST One Spot Left'")[0][0]
full = sql("select event_id from events where title='TEST Full Event'")[0][0]
started = sql("select event_id from events where title='TEST Started Event'")[0][0]
s, _ = call(anon, "post", f"/api/rsvps/{free}")
check("FR-05 RSVP needs login (401)", s == 401, s)
s, _ = call(bob, "post", f"/api/rsvps/{free}")
check("FR-05 RSVP succeeds with a spot left", s in (200, 201), s)
s, d = call(bob, "get", f"/api/events/{free}")
check("FR-05 count updated and seats left 0", d["activeRSVPCount"] == 2 and d["seatsLeft"] == 0, d)
s, _ = call(bob, "post", f"/api/rsvps/{free}")
check("FR-05 duplicate RSVP is not counted twice", s == 200, s)
check("FR-05 no duplicate rows", sql("select count(*) from rsvps where event_id=?", free)[0][0] == 2)
s, _ = call(app.test_client(), "post", "/api/rsvps/1")
check("FR-05 anonymous still 401", s == 401, s)
carol = app.test_client(); login(carol, "cara@example.com", "longenough1")
s, _ = call(carol, "post", f"/api/rsvps/{full}")
check("FR-06 full event rejected (409)", s == 409, s)
s, _ = call(carol, "post", f"/api/rsvps/{started}")
check("FR-06 started event rejected (409)", s == 409, s)
s, _ = call(carol, "post", "/api/rsvps/99999")
check("FR-06 unknown event -> 404", s == 404, s)
check("FR-06 count never exceeds capacity", sql("select count(*) from events e where (select count(*) from rsvps r where r.event_id=e.event_id) > e.capacity")[0][0] == 0)
s, r = call(bob, "get", "/api/rsvps")
check("FR-07 My RSVPs lists Bob's events", s == 200 and any(x["id"] == free for x in r))
check("FR-07 shows participation status", all(x.get("participation") == "Confirmed" for x in r))
s, r = call(carol, "get", "/api/rsvps")
check("FR-07 new user sees empty list", s == 200 and r == [])

# FR-05 race: only one winner for the last seat
race_ev = None
s, ne = call(alice, "post", "/api/events", title="Race", description="d", location="l", categoryId=1,
             date="2030-05-01", startTime="10:00", endTime="11:00", capacity=1)
race_ev = ne["id"]
codes = []
cl = [bob, carol]
def go(cc):
    codes.append(call(cc, "post", f"/api/rsvps/{race_ev}")[0])
ts = [threading.Thread(target=go, args=(x,)) for x in cl]
[t.start() for t in ts]; [t.join() for t in ts]
check("FR-05/06 simultaneous last-seat RSVP: exactly one wins", sorted(codes)[0] in (200, 201) and codes.count(409) == 1, codes)

# FR-08 error vs empty handled in browser tests (AC-08.3)

# FR-09 Create
good = dict(title="Mine", description="d", location="l", categoryId=1, date="2030-06-01", startTime="09:00", endTime="10:00", capacity=10)
s, _ = call(anon, "post", "/api/events", **good)
check("FR-09 create needs login (401)", s == 401, s)
s, ce = call(alice, "post", "/api/events", **good)
check("FR-09 create ok (201)", s == 201, s)
for label, patch in [("missing title", dict(title="")), ("end before start", dict(endTime="08:00")), ("past date", dict(date="2000-01-01")),
                     ("capacity 0", dict(capacity=0)), ("bad category", dict(categoryId=999)), ("bad date format", dict(date="01/06/2030"))]:
    s, _ = call(alice, "post", "/api/events", **{**good, **patch})
    check(f"FR-09 invalid ({label}) -> 400", s == 400, s)
s, _ = call(alice, "get", "/api/events?q=Mine")
check("FR-09 new event appears in browse", any(x["title"] == "Mine" for x in _))

# FR-10 Edit
eid = ce["id"]
s, _ = call(bob, "put", f"/api/events/{eid}", **{**good, "title": "Hacked"})
check("FR-10 non-owner cannot edit (403)", s == 403, s)
s, _ = call(anon, "put", f"/api/events/{eid}", **good)
check("FR-10 anonymous edit (401)", s == 401, s)
s, _ = call(alice, "put", f"/api/events/{eid}", **{**good, "title": "Renamed"})
check("FR-10 owner edit ok", s == 200, s)
call(bob, "post", f"/api/rsvps/{eid}")
call(carol, "post", f"/api/rsvps/{eid}")
s, _ = call(alice, "put", f"/api/events/{eid}", **{**good, "capacity": 1})
check("FR-10 capacity below current RSVPs -> 400", s == 400, s)
s, _ = call(alice, "put", f"/api/events/{eid}", **{**good, "capacity": 2})
check("FR-10 capacity equal to RSVPs ok", s == 200, s)
s, _ = call(alice, "put", f"/api/events/{started}", **good)
check("FR-10 started event cannot be edited", s in (403, 409), s)

# NFR-07 failure mid-RSVP rolls back
from db import connection as dbc  # noqa: E402
before = sql("select count(*) from rsvps")[0][0]
try:
    with dbc.transaction() as conn:
        conn.execute("INSERT INTO rsvps (user_id, event_id) VALUES (1, 2)")
        raise RuntimeError("simulated failure")
except RuntimeError:
    pass
check("NFR-07 simulated failure leaves no partial RSVP", sql("select count(*) from rsvps")[0][0] == before)

# NFR-06 layering
def imports(path):
    return open(os.path.join(BACKEND, path), encoding="utf-8").read()
bad = []
for f in os.listdir(os.path.join(BACKEND, "routes")):
    if f.endswith(".py") and re.search(r"sqlite3|from db|import db|SELECT |INSERT ", imports("routes/" + f)):
        bad.append("routes/" + f)
for f in os.listdir(os.path.join(BACKEND, "services")):
    if f.endswith(".py") and re.search(r"sqlite3|SELECT |INSERT |UPDATE ", imports("services/" + f)):
        bad.append("services/" + f)
check("NFR-06 no SQL in routes/services; routes never touch db", not bad, bad)

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
