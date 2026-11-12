"""Security checks for NFR-02, NFR-03, NFR-07 and NFR-08.

Run from backend/:   python tests/security_check.py
Uses a throwaway database and key, so it never touches real data.
"""
import hashlib
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
DB = os.path.join(TMP, "security.db")
os.environ["EVENTS_DB"] = DB
os.environ["SECRET_KEY_FILE"] = os.path.join(TMP, "secret_key")
os.environ.pop("SECRET_KEY", None)
sys.path.insert(0, BACKEND)
subprocess.run([sys.executable, "seed.py"], cwd=BACKEND, env=os.environ, check=True, capture_output=True)

from app import app  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"   -> {detail}"))
    if not ok:
        fails.append(name)


def call(client, method, url, **body):
    token = client.get("/api/csrf-token").get_json()["csrfToken"]
    kwargs = {"headers": {"X-CSRFToken": token}}
    if method != "get":
        kwargs["json"] = body
    resp = getattr(client, method)(url, **kwargs)
    return resp.status_code, resp.get_json(silent=True)


def login(client, email):
    return call(client, "post", "/api/auth/login", email=email, password="password123")


def db(sql, *args):
    conn = sqlite3.connect(DB)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


alice, bob, anon = app.test_client(), app.test_client(), app.test_client()
login(alice, "alice@example.com")
login(bob, "bob@example.com")
FUTURE = "2030-01-15"
GOOD_EVENT = dict(title="Security Test", description="d", location="l", categoryId=1,
                  date=FUTURE, startTime="10:00", endTime="11:00", capacity=5)

print("\n== NFR-08: CSRF ==")
write_methods = {"POST", "PUT", "DELETE", "PATCH"}
bad = []
count = 0
for rule in app.url_map.iter_rules():
    if rule.endpoint == "static":
        continue
    for method in sorted(rule.methods & write_methods):
        count += 1
        url = re.sub(r"<[^>]+>", "1", rule.rule)
        status = getattr(alice, method.lower())(url, json={}).status_code
        if status != 400:
            bad.append((method, url, status))
check(f"all {count} state-changing routes refuse a request with no CSRF token", not bad, bad)
n_events = db("select count(*) from events")[0][0]
status = alice.post("/api/events", json=GOOD_EVENT).status_code
check("create-event without token -> refused, no listing", status == 400 and db("select count(*) from events")[0][0] == n_events)

print("\n== NFR-03: login and ownership enforced on the server ==")
protected = [("get", "/api/favorites"), ("get", "/api/rsvps"), ("post", "/api/favorites/1"),
             ("delete", "/api/favorites/1"), ("post", "/api/rsvps/1"), ("post", "/api/events"),
             ("put", "/api/events/1")]
codes = {f"{m} {u}": call(anon, m, u, **GOOD_EVENT)[0] for m, u in protected}
check("signed-out requests to every protected route -> 401", all(c == 401 for c in codes.values()), codes)
call(alice, "post", "/api/favorites/1")
call(alice, "post", "/api/rsvps/1")
check("another user cannot edit someone's event (403, unchanged)",
      call(bob, "put", "/api/events/1", **GOOD_EVENT)[0] == 403
      and db("select title from events where event_id = 1")[0][0] != "Security Test")
check("another user cannot remove someone's favorite", call(bob, "delete", "/api/favorites/1")[0] == 404
      and db("select count(*) from favorites where user_id = 1 and event_id = 1")[0][0] == 1)
check("favorites and RSVP lists are private",
      bob.get("/api/favorites").get_json()["count"] == 0
      and all(e["id"] != 1 for e in bob.get("/api/rsvps").get_json()["events"]))

print("\n== NFR-08: SQL injection ==")
payloads = ["' OR '1'='1", "'; DROP TABLE users;--", '" OR 1=1 --', "1; SELECT * FROM users", "%", "_"]
tables_before = sorted(r[0] for r in db("select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"))
results = []
for p in payloads:
    r1 = alice.get("/api/events", query_string={"q": p})
    r2 = alice.get("/api/events", query_string={"categories": p})
    r3 = alice.get("/api/events", query_string={"startDate": p})
    results.append((p, r1.status_code, r1.get_json()["count"], r2.status_code, r2.get_json()["count"], r3.status_code))
check("search and category payloads match nothing", all(r[1] == 200 and r[2] == 0 and r[3] == 200 and r[4] == 0 for r in results), results)
check("date payloads are rejected with 400", all(r[5] == 400 for r in results), results)
login_codes = [call(anon, "post", "/api/auth/login", email=p, password=p)[0] for p in payloads]
check("login with payloads -> 401, no session", all(c == 401 for c in login_codes), login_codes)
status, body = call(anon, "post", "/api/auth/register", displayName="' OR '1'='1", email="sqli@example.com", password="password123")
check("payload as display name is stored as plain text", status == 201 and db("select name from users where email = 'sqli@example.com'")[0][0] == "' OR '1'='1")
status, body = call(bob, "post", "/api/events", **{**GOOD_EVENT, "title": "' OR '1'='1", "description": "'; DROP TABLE users;--"})
found = bob.get("/api/events", query_string={"q": "' OR '1'='1"}).get_json()
check("payload as event title: stored literally, search finds exactly that one", status == 201 and found["count"] == 1 and found["events"][0]["title"] == "' OR '1'='1", found)
tables_after = sorted(r[0] for r in db("select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"))
check("all tables still exist, users intact", tables_before == tables_after and db("select count(*) from users")[0][0] >= 3)

print("\n== NFR-08: scripts shown as text ==")
status, body = call(bob, "post", "/api/events", **{**GOOD_EVENT, "title": "<script>alert(1)</script>"})
resp = bob.get(f"/api/events/{body['event']['id']}")
check("script tag stored and returned as plain text in JSON", status == 201 and resp.get_json()["event"]["title"] == "<script>alert(1)</script>"
      and resp.content_type.startswith("application/json") and resp.headers.get("X-Content-Type-Options") == "nosniff")

print("\n== NFR-02: password storage ==")
for email in ("pw1@example.com", "pw2@example.com"):
    call(anon, "post", "/api/auth/register", displayName="Pw", email=email, password="SamePassword1")
hashes = [r[0] for r in db("select password_hash from users where email in ('pw1@example.com','pw2@example.com')")]
check("same password -> two different salted hashes, never plaintext",
      len(hashes) == 2 and hashes[0] != hashes[1] and all("SamePassword1" not in h for h in hashes)
      and all(h.startswith(("scrypt:", "pbkdf2:")) for h in hashes), hashes)
check("both accounts can log in",
      all(call(app.test_client(), "post", "/api/auth/login", email=e, password="SamePassword1")[0] == 200
          for e in ("pw1@example.com", "pw2@example.com")))

print("\n== Sessions and secret key ==")
secret = app.config["SECRET_KEY"]
check("secret key is random, not the old hardcoded one", secret != "dev-only-change-me" and len(secret) >= 32)
try:
    from flask.json.tag import TaggedJSONSerializer
    from itsdangerous import URLSafeTimedSerializer
    forger = URLSafeTimedSerializer("dev-only-change-me", salt="cookie-session", serializer=TaggedJSONSerializer(),
                                    signer_kwargs={"key_derivation": "hmac", "digest_method": hashlib.sha1})
    forged = forger.dumps({"user_id": 1})
    victim = app.test_client()
    victim.set_cookie("session", forged)
    check("a cookie forged with the old default key is ignored", victim.get("/api/auth/me").get_json()["user"] is None)
except Exception as exc:  # pragma: no cover
    check("forged-cookie test could run", False, exc)
fresh = app.test_client()
tok = fresh.get("/api/csrf-token")
cookie = " ".join(tok.headers.getlist("Set-Cookie"))
check("session cookie is HttpOnly and SameSite=Lax", "HttpOnly" in cookie and "SameSite=Lax" in cookie, cookie)
check("debug mode is off", app.debug is False)

print("\n== Headers ==")
for path in ("/", "/api/events", "/js/app.js"):
    h = anon.get(path).headers
    ok = ("script-src 'self'" in h.get("Content-Security-Policy", "") and h.get("X-Content-Type-Options") == "nosniff"
          and h.get("X-Frame-Options") == "DENY" and h.get("Referrer-Policy") == "same-origin")
    check(f"security headers on {path}", ok, dict(h))
check("API responses are not cacheable", anon.get("/api/favorites").headers.get("Cache-Control") == "no-store")

print("\n== Files that must not be reachable ==")
paths = ["/../backend/app.py", "/..%2fbackend%2fapp.py", "/%2e%2e/backend/seed.py", "/backend/app.py",
         "/events.db", "/.secret_key", "/schema.sql", "/app.py"]
codes = {p: anon.get(p).status_code for p in paths}
check("backend code, database and key are not served", all(c == 404 for c in codes.values()), codes)

print("\n== Size and input limits ==")
big = anon.post("/api/auth/login", data="x" * 70000, content_type="application/json",
                headers={"X-CSRFToken": anon.get("/api/csrf-token").get_json()["csrfToken"]})
check("request body over 64 KB -> 413 JSON", big.status_code == 413 and big.get_json() is not None, big.status_code)
check("search text over 200 chars -> 400", alice.get("/api/events", query_string={"q": "a" * 201}).status_code == 400)
many = alice.get("/api/events?" + "&".join(f"categories=c{i}" for i in range(3000)))
check("3000 category values -> handled, no server error", many.status_code == 200, many.status_code)
check("display name over 100 chars -> 400", call(anon, "post", "/api/auth/register", displayName="n" * 101, email="long@example.com", password="password123")[0] == 400)
check("email over 254 chars -> 400", call(anon, "post", "/api/auth/register", displayName="n", email="e" * 250 + "@x.com", password="password123")[0] == 400)

print("\n== NFR-07: errors are JSON, not error pages ==")
check("bad JSON body -> JSON error, not a server page", call(anon, "post", "/api/auth/login")[1] is not None)
check("unknown API path -> JSON 404", anon.get("/api/nothing").get_json() == {"error": "Not found."})

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)
