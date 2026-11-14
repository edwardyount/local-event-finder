"""Reset the database and load the test plan's Test Data (the P-DEV test cases call it the seed).

    python seed_testplan.py                # categories, accounts A, B, O, P, 16 events, 6 RSVPs
    python seed_testplan.py --no-events    # categories and the four accounts only (US08_TC_03)
    python seed_testplan.py --performance  # the fixture data plus 500 generated events (NFR01_TC_01)

Every account's password is Passw0rd. T is today's date on the US Eastern clock, the app's
single time zone, so the dates come out right whatever time zone the laptop is set to.
Before COMMIT the script reads everything back and checks it against the tables in this
script, which copy the test plan's Test Data; after any edit to those tables, check them
against the test plan again. If a check fails, nothing is loaded and it exits 1. seed.py is
unchanged and still loads its own data. Set EVENTS_DB to load a different database file, as
the app does.
"""
import argparse
import os
import random
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from werkzeug.security import check_password_hash, generate_password_hash

from db.connection import DB_PATH, get_connection, init_db
from seed import CATEGORIES

try:
    EASTERN = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError:
    # Windows has no system time zone data; the tzdata package supplies it.
    raise SystemExit("Time zone data missing. Run: pip install -r requirements.txt")

PASSWORD = "Passw0rd"

# (account, email, display name), in the order of the Test Data's accounts table
ACCOUNTS = [
    ("A", "usera@example.com", "Tester A"),
    ("B", "userb@example.com", "Tester B"),
    ("O", "organizer@example.com", "Test Organizer"),
    ("P", "participant@example.com", "Test Participant"),
]

# (fixture, title, category, days after T, start, end, capacity, owner, description, location)
# in the order of the Test Data's events table, which is not start order on purpose.
# Event C (cancelled) is not loaded: this build has no way to cancel an event.
EVENTS = [
    ("E1", "Lakeside Yoga Session", "Sports and Fitness", 5, "09:00", "10:00", 20, "O",
     "A gentle morning stretch class by the lake. Bring a mat.", "Lakeside Park Pavilion"),
    ("E2", "Book Swap", "Community and Volunteering", 3, "13:00", "15:00", 20, "O",
     "Bring a book you have finished and take a new one home.", "Brightwater Library"),
    ("E3", "Trivia Night", "Social and Recreation", 4, "19:00", "21:00", 20, "O",
     "Teams of four answer quiz rounds.", "Riverside Tavern"),
    ("EA", "Pottery Workshop", "Arts and Culture", 9, "10:00", "12:00", 10, "A",
     "Shape and glaze a bowl to show at the craft market.", "Clay Studio, Elm Street"),
    ("EB", "Chess Club Meetup", "Social and Recreation", 6, "18:00", "20:00", 10, "A",
     "Casual games for every level. Boards are provided.", "Elm Street Community Room"),
    ("EX", "Board Game Afternoon", "Social and Recreation", 8, "14:00", "16:00", 10, "B",
     "Play modern board games and meet new people.", "Maple Hall"),
    ("F", "Cooking Class", "Food and Drink", 7, "17:00", "19:00", 2, "O",
     "Cook a seasonal dish with produce from the farmers market.", "Teaching Kitchen, Oak Avenue"),
    ("FE", "Jazz Evening", "Arts and Culture", 2, "20:00", "22:00", 1, "O",
     "A live jazz trio plays two sets.", "Blue Room Lounge"),
    ("R", "Coding Basics", "Education", 11, "16:00", "18:00", 15, "O",
     "Write your first program in Python. Laptops are provided.", "Tech Hub, Room 2"),
    ("S", "Sunrise Walk", "Sports and Fitness", 0, "00:01", "23:59", 20, "O",
     "An easy walk around the reservoir at first light.", "Reservoir Trailhead"),
    ("Range 1", "Study Skills Talk", "Education", 13, "18:00", "19:00", 30, "O",
     "Tips for planning revision and taking notes.", "Learning Center, Room 101"),
    ("Range 2", "Science Fair", "Education", 14, "09:00", "11:00", 30, "O",
     "Students show their science projects.", "School Gymnasium"),
    ("Range 3", "Mural Painting", "Arts and Culture", 14, "11:00", "13:00", 30, "O",
     "Help paint a community mural on the park wall.", "Pine Street Park"),
    ("Range 4", "Robotics Demo", "Education", 15, "15:00", "16:00", 30, "O",
     "Watch student robots finish an obstacle course.", "Engineering Lab"),
    ("Range 5", "Street Food Night", "Food and Drink", 16, "20:00", "22:00", 30, "O",
     "Food trucks serve dishes from around the world.", "Main Street Plaza"),
    ("Range 6", "Bakery Tour", "Food and Drink", 17, "10:00", "11:00", 30, "O",
     "See how bread is baked and taste fresh loaves.", "Corner Bakery, Pine Street"),
]

# (account, fixture): every RSVP is active
RSVPS = [("B", "E3"), ("B", "EA"), ("P", "EA"), ("P", "F"), ("P", "FE"), ("P", "R")]

# What the self-check expects, written out from the Test Data, not computed from EVENTS.
TERM_PLACES = {
    "bRiGhTwAtEr": {("E2", "location")},
    "yOgA": {("E1", "title")},
    "QUIZ": {("E3", "description")},
    "market": {("F", "description"), ("EA", "description")},
    "zzqxv": set(),
    "concert": set(),   # plus the titles of every tenth performance event
}
ACTIVE_RSVPS = {"E3": 1, "EA": 2, "F": 1, "FE": 1, "R": 1}   # every other event has 0
FREE_PLACES = {"F": 1, "FE": 0}
STARTED = "S"
D1, D2 = 14, 16   # days after T
NOT_REGISTERED = ["newuser1@example.com", "mismatch1@example.com", "short1@example.com",
                  "blank1@example.com", "hash1@example.com", "hash2@example.com",
                  "nobody@example.com"]
COUNTS = {   # table: (no options, --no-events, --performance)
    "users": (4, 4, 4), "categories": (6, 6, 6), "events": (16, 0, 516),
    "rsvps": (6, 0, 6), "favorites": (0, 0, 0),
}

# Performance set: words that contain none of the search terms
PERF_COUNT = 500
PERF_TOPICS = ["Chess", "Pottery", "Painting", "Coding", "Gardening", "Hiking", "Film",
               "Baking", "Robotics", "Poetry"]
PERF_KINDS = ["Meetup", "Workshop", "Social", "Class", "Walk", "Fair", "Talk", "Tournament"]
PERF_PLACES = ["Maple Hall", "Oak Street Field", "Pine Street Center", "Riverside Pavilion",
               "Elm Street Studio", "Cedar Room"]
MODES = ("default", "no-events", "performance")


def iso(today, offset):
    return (today + timedelta(days=offset)).isoformat()


def us_date(day):
    return f"{day[5:7]}/{day[8:10]}/{day[0:4]}"   # mm/dd/yyyy, as a US Chrome date field shows


def load_accounts(conn):
    users = {}
    for letter, email, name in ACCOUNTS:
        # one hash per account, so each stored hash has its own salt (NFR02_TC_01)
        cur = conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                           (name, email, generate_password_hash(PASSWORD)))
        users[letter] = cur.lastrowid
    return users


def load_events(conn, today, users, cat):
    events = {}
    for name, title, c, off, st, en, capy, owner, desc, loc in EVENTS:
        cur = conn.execute(
            """INSERT INTO events (title, description, date, start_time, end_time,
                                   location, capacity, category_id, creator_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, desc, iso(today, off), st, en, loc, capy, cat[c], users[owner]))
        events[name] = cur.lastrowid
    for who, name in RSVPS:
        conn.execute("INSERT INTO rsvps (user_id, event_id, status) VALUES (?, ?, 'active')",
                     (users[who], events[name]))
    return events


def load_performance(conn, today, organizer, cat):
    """500 upcoming events dated T+18 to T+120, after every fixture event; every tenth is a concert."""
    rng = random.Random(350)
    cat_ids = sorted(cat.values())
    concerts = set()
    for i in range(PERF_COUNT):
        topic = rng.choice(PERF_TOPICS)
        kind = "Concert" if i % 10 == 0 else rng.choice(PERF_KINDS)
        h = rng.randint(8, 19)
        cur = conn.execute(
            """INSERT INTO events (title, description, date, start_time, end_time,
                                   location, capacity, category_id, creator_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"{topic} {kind} #{i}", f"Performance test event {i} about {topic.lower()}.",
             iso(today, rng.randint(18, 120)), f"{h:02d}:00", f"{h + 1:02d}:00",
             rng.choice(PERF_PLACES), rng.randint(10, 200), rng.choice(cat_ids), organizer))
        if kind == "Concert":
            concerts.add(cur.lastrowid)
    return concerts


def parses(value, fmt):
    try:
        return datetime.strptime(value, fmt).strftime(fmt) == value
    except (TypeError, ValueError):
        return False


def self_check(conn, mode, today, users, events, concerts):
    """Read the data back by SQL. Returns (lines to print, number of failed checks)."""
    lines, failed = [], 0
    col = MODES.index(mode)
    names = {eid: name for name, eid in events.items()}

    def label(eid):
        return names.get(eid, f"event {eid}")

    def report(n, what, problems):
        nonlocal failed
        if problems:
            failed += 1
            lines.append((n, [f"check {n} FAIL: {what}"] + [f"    {p}" for p in problems]))
        else:
            lines.append((n, [f"check {n} PASS: {what}"]))

    def not_applicable(n, what):
        lines.append((n, [f"check {n} does not apply with --no-events: {what}"]))

    def in_order():
        return [line for _, block in sorted(lines) for line in block], failed

    rows = conn.execute(
        """SELECT e.*, c.category_name, u.email AS owner_email FROM events e
             JOIN categories c ON c.category_id = e.category_id
             JOIN users u ON u.user_id = e.creator_id ORDER BY e.event_id""").fetchall()
    now = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M")

    def started(r):
        return f"{r['date']} {r['start_time']}" <= now

    # 1. row counts
    problems = []
    for table, expected in COUNTS.items():
        got = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if got != expected[col]:
            problems.append(f"{table}: {got}, expected {expected[col]}")
    report(1, "row counts", problems)

    # 2. each search term sits exactly where the Test Data puts it (title, description, location)
    problems = []
    for term, places in TERM_PLACES.items():
        expected = set() if mode == "no-events" else {(events[n], f) for n, f in places}
        if term == "concert":
            expected |= {(eid, "title") for eid in concerts}
        found = {(r["event_id"], f) for r in rows for f in ("title", "description", "location")
                 if term.lower() in r[f].lower()}
        for eid, f in sorted(found - expected):
            problems.append(f"{term}: found in {label(eid)} {f}, where the Test Data has no {term}")
        for eid, f in sorted(expected - found):
            problems.append(f"{term}: missing from {label(eid)} {f}")
    if mode == "performance" and len(concerts) != PERF_COUNT // 10:
        problems.append(f"concert: {len(concerts)} performance events, expected {PERF_COUNT // 10}")
    report(2, "search terms placed only as the Test Data says", problems)

    # 8. no registration input is registered; every email is trimmed and lowercased
    problems = []
    for email in NOT_REGISTERED:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            problems.append(f"{email} is registered")
    for r in conn.execute("SELECT email FROM users"):
        if r["email"] != r["email"].strip().lower():
            problems.append(f"{r['email']!r} is not trimmed and lowercased")
    report(8, "registration emails unused; emails trimmed and lowercased", problems)

    # 9. each account's hash accepts Passw0rd, refuses passw0rd, and has its own salt
    problems = []
    hashes = [r["password_hash"] for r in conn.execute("SELECT password_hash FROM users")]
    for r in conn.execute("SELECT email, password_hash FROM users"):
        if not check_password_hash(r["password_hash"], PASSWORD):
            problems.append(f"{r['email']}: hash refuses {PASSWORD}")
        if check_password_hash(r["password_hash"], PASSWORD.lower()):
            problems.append(f"{r['email']}: hash accepts {PASSWORD.lower()}")
    if len(set(hashes)) != len(hashes):
        problems.append("two accounts share one password hash")
    report(9, "password hashes", problems)

    if mode == "no-events":
        for n, what in ((3, "started and upcoming"), (4, "RSVPs"), (5, "categories and date range"),
                        (6, "stored order"), (7, "event IDs"), (10, "form rules"),
                        (11, "stored values")):
            not_applicable(n, what)
        return in_order()

    # 3. S has started and every other event is upcoming, on the Eastern clock
    problems = []
    for r in rows:
        if r["event_id"] == events[STARTED] and not started(r):
            problems.append(f"S has not started at {now} Eastern: load after 00:01 Eastern")
        elif r["event_id"] != events[STARTED] and started(r):
            problems.append(f"{label(r['event_id'])} has already started at {now} Eastern")
    report(3, "S started, every other event upcoming", problems)

    # 4. active RSVPs per event; F has one free place, FE none
    problems = []
    letter = {uid: a for a, uid in users.items()}
    pairs = {(letter[r["user_id"]], label(r["event_id"]))
             for r in conn.execute("SELECT user_id, event_id FROM rsvps WHERE status = 'active'")}
    if pairs != set(RSVPS):
        problems.append(f"active RSVPs {sorted(pairs)}, expected {sorted(RSVPS)}")
    if conn.execute("SELECT COUNT(*) FROM rsvps WHERE status != 'active'").fetchone()[0]:
        problems.append("an RSVP is not active")
    for r in rows:
        n = conn.execute("SELECT COUNT(*) FROM rsvps WHERE event_id = ? AND status = 'active'",
                         (r["event_id"],)).fetchone()[0]
        name = label(r["event_id"])
        if n != ACTIVE_RSVPS.get(name, 0):
            problems.append(f"{name}: {n} active RSVPs, expected {ACTIVE_RSVPS.get(name, 0)}")
        if name in FREE_PLACES and r["capacity"] - n != FREE_PLACES[name]:
            problems.append(f"{name}: {r['capacity'] - n} free places, expected {FREE_PLACES[name]}")
    report(4, "RSVPs as the events table says", problems)

    # 5. every category has an upcoming event; no Sports and Fitness event from D1 to D2
    problems = []
    for c in conn.execute("SELECT category_name FROM categories"):
        if not any(r["category_name"] == c[0] and not started(r) for r in rows):
            problems.append(f"{c[0]} has no upcoming event")
    for r in rows:
        if (r["category_name"] == "Sports and Fitness"
                and iso(today, D1) <= r["date"] <= iso(today, D2)):
            problems.append(f"{label(r['event_id'])} is Sports and Fitness between D1 and D2")
    report(5, "categories and the D1 to D2 range", problems)

    # 6. stored order is not start order, so an unsorted list shows it
    by_id = [r["event_id"] for r in rows]
    by_start = [r["event_id"] for r in sorted(rows, key=lambda r: (r["date"], r["start_time"],
                                                                   r["event_id"]))]
    report(6, "stored order differs from start order",
           ["events are stored in start order"] if by_id == by_start else [])

    # 7. the seed never uses event ID 99999
    top = max(by_id)
    report(7, "every event ID below 99999", [f"largest event ID is {top}"] if top >= 99999 else [])

    # 10. every row passes the build's own form rules (event_manage_service._clean)
    problems = []
    for r in rows:
        name = label(r["event_id"])
        for f, limit in (("title", 200), ("description", 5000), ("location", 300)):
            v = r[f]
            if not v.strip() or len(v) > limit or v != v.strip():
                problems.append(f"{name}: {f} breaks the form rule (1 to {limit}, trimmed)")
        if not parses(r["date"], "%Y-%m-%d"):
            problems.append(f"{name}: date {r['date']!r} is not YYYY-MM-DD")
        if not (parses(r["start_time"], "%H:%M") and parses(r["end_time"], "%H:%M")):
            problems.append(f"{name}: a time is not HH:MM")
        elif r["end_time"] <= r["start_time"]:
            problems.append(f"{name}: end {r['end_time']} is not after start {r['start_time']}")
        if not (isinstance(r["capacity"], int) and 1 <= r["capacity"] <= 100000):
            problems.append(f"{name}: capacity {r['capacity']!r} is outside 1 to 100000")
    report(10, "every event passes the form rules", problems)

    # 11. accounts and fixture events read back equal the tables above
    problems = []
    stored = [tuple(r) for r in conn.execute("SELECT email, name FROM users ORDER BY user_id")]
    if stored != [(e, n) for _, e, n in ACCOUNTS]:
        problems.append(f"accounts {stored}")
    email = {a: e for a, e, _ in ACCOUNTS}
    by_eid = {r["event_id"]: r for r in rows}
    for name, title, c, off, st, en, capy, owner, desc, loc in EVENTS:
        r = by_eid.get(events[name])
        want = (title, c, iso(today, off), st, en, capy, email[owner], desc, loc, "active")
        got = r and (r["title"], r["category_name"], r["date"], r["start_time"], r["end_time"],
                     r["capacity"], r["owner_email"], r["description"], r["location"],
                     r["event_status"])
        if got != want:
            problems.append(f"{name}: stored {got}, expected {want}")
    report(11, "stored values equal the Test Data", problems)
    return in_order()


def print_tables(conn, mode, today, users, events, concerts, loaded_at):
    """Everything printed here is read back from the database after COMMIT."""
    print("Database:", DB_PATH)
    print(f"Loaded at {loaded_at} Eastern")
    print(f"T  = {iso(today, 0)}  ({us_date(iso(today, 0))})")
    print(f"D1 = {iso(today, D1)}  ({us_date(iso(today, D1))})")
    print(f"D2 = {iso(today, D2)}  ({us_date(iso(today, D2))})")
    print()
    letter = {uid: a for a, uid in users.items()}
    print("Account  User ID  Email                    Display name")
    for r in conn.execute("SELECT user_id, email, name FROM users ORDER BY user_id"):
        print(f"{letter[r['user_id']]:<8} {r['user_id']:<8} {r['email']:<24} {r['name']}")
    if mode != "no-events":
        names = {eid: name for name, eid in events.items()}
        rows = conn.execute(
            """SELECT e.*, c.category_name,
                      (SELECT COUNT(*) FROM rsvps r WHERE r.event_id = e.event_id
                          AND r.status = 'active') AS rsvps
                 FROM events e JOIN categories c ON c.category_id = e.category_id
                WHERE e.event_id IN (%s) ORDER BY e.event_id""" % ",".join("?" * len(events)),
            list(events.values())).fetchall()
        print()
        print("Fixture  ID  Title                  Category                    Date        "
              "Start  End    Cap  RSVPs  Owner")
        for r in rows:
            print(f"{names[r['event_id']]:<8} {r['event_id']:<3} {r['title']:<22} "
                  f"{r['category_name']:<27} {r['date']}  {r['start_time']}  {r['end_time']}  "
                  f"{r['capacity']:<4} {r['rsvps']:<6} {letter[r['creator_id']]}")
        print()
        print("Fixture  Description | Location")
        for r in rows:
            print(f"{names[r['event_id']]:<8} {r['description']} | {r['location']}")
        print()
        print("Event C (cancelled) is not loaded: this build has no way to cancel an event.")
        print("Event ID 99999 does not exist.")
    if mode == "performance":
        low, high, first, last = conn.execute(
            "SELECT MIN(event_id), MAX(event_id), MIN(date), MAX(date) FROM events "
            "WHERE event_id > ?", (max(events.values()),)).fetchone()
        n = conn.execute("SELECT COUNT(*) FROM events WHERE instr(lower(title), 'concert') > 0"
                         ).fetchone()[0]
        print(f"Performance set: {high - low + 1} events, IDs {low} to {high}, dated {first} "
              f"to {last}, {n} with concert in the title, all owned by account O")
    print()
    for t in COUNTS:
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])


def main():
    parser = argparse.ArgumentParser(description="Load the test plan's Test Data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--no-events", action="store_true",
                       help="categories and the four accounts only (US08_TC_03)")
    group.add_argument("--performance", action="store_true",
                       help="also 500 generated upcoming events (NFR01_TC_01)")
    args = parser.parse_args()
    mode = "no-events" if args.no_events else "performance" if args.performance else "default"

    if os.path.exists(DB_PATH):
        if not os.access(DB_PATH, os.W_OK):   # NFR07_TC_01 makes the file read-only
            print(f"{DB_PATH} is read-only. Clear its read-only setting, then run again.")
            sys.exit(1)
        try:
            os.remove(DB_PATH)
        except PermissionError:
            print(f"Close the program that has {DB_PATH} open, then run again.")
            sys.exit(1)
    init_db()

    loaded = datetime.now(EASTERN)
    today = loaded.date()   # T: the Eastern date, not the laptop's
    conn = get_connection()
    conn.execute("BEGIN")
    conn.executemany(
        "INSERT INTO categories (category_name, category_image) VALUES (?, ?)", CATEGORIES)
    cat = {r["category_name"]: r["category_id"] for r in conn.execute("SELECT * FROM categories")}
    users = load_accounts(conn)
    events, concerts = {}, set()
    if mode != "no-events":
        events = load_events(conn, today, users, cat)
    if mode == "performance":
        concerts = load_performance(conn, today, users["O"], cat)

    lines, failed = self_check(conn, mode, today, users, events, concerts)
    print("\n".join(lines))
    if failed:
        conn.execute("ROLLBACK")
        conn.close()
        print(f"self-check FAIL ({failed} check(s))")
        print("DATABASE NOT LOADED: do not test")
        sys.exit(1)
    conn.execute("COMMIT")
    print()
    print_tables(conn, mode, today, users, events, concerts, loaded.strftime("%Y-%m-%d %H:%M"))
    conn.close()
    print()
    print("self-check PASS")
    print("Sign every browser out and back in: a session left signed in now belongs to "
          "whichever account has its user ID.")


if __name__ == "__main__":
    main()
