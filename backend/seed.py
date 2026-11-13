"""Reset the database and load test data.

    python seed.py            # categories, 2 test users, sample + test events
    python seed.py --bulk     # also add 500 random events (NFR-01 timing test)
"""
import os
import random
import sys
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from db.connection import DB_PATH, get_connection, init_db

CATEGORIES = [
    ("Arts and Culture",           "/images/events/louisville-art-walk.jpg"),
    ("Sports and Fitness",         "/images/events/fitness-meetup.jpg"),
    ("Education",                  "/images/events/data-science.jpg"),
    ("Community and Volunteering", "/images/events/volunteer-day.jpg"),
    ("Food and Drink",             "/images/events/food-festival.jpg"),
    ("Social and Recreation",      "/images/events/board-game-night.jpg"),
]
#min 8 char
TEST_PASSWORD = "password123" 


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def seed_core(conn):
    conn.executemany(
        "INSERT INTO categories (category_name, category_image) VALUES (?, ?)", CATEGORIES)

    pw = generate_password_hash(TEST_PASSWORD)
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 ("Alice Tester", "alice@example.com", pw))
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 ("Bob Tester", "bob@example.com", pw))

    cat = {r["category_name"]: r["category_id"]
           for r in conn.execute("SELECT * FROM categories")}

    # (title, description, location, category, day offset, start, end, capacity, creator_id)
    events = [
        ("Louisville Art Walk", "Explore local artists, creative exhibits and galleries.",
         "NuLu, Louisville", "Arts and Culture", 3, "14:00", "17:00", 100, 1),
        ("Saturday Fitness Meetup", "Join a community workout and meet new fitness enthusiasts.",
         "Waterfront Park, Louisville", "Sports and Fitness", 4, "09:00", "11:00", 50, 1),
        ("Introduction to Data Science", "Learn about data analytics, technology and career opportunities.",
         "University of Louisville", "Education", 7, "16:00", "18:00", 75, 2),
        ("Community Volunteer Day", "Give back to the community through a local volunteer initiative.",
         "Downtown Louisville", "Community and Volunteering", 9, "10:00", "13:00", 60, 2),
        ("Louisville Food Festival", "Discover local restaurants, food vendors and new flavors.",
         "Fourth Street Live, Louisville", "Food and Drink", 10, "12:00", "16:00", 150, 1),
        ("Board Game Social Night", "Meet new people and enjoy a relaxed evening of games.",
         "Highlands, Louisville", "Social and Recreation", 11, "18:00", "21:00", 40, 2),
        # --- test fixtures ---
        ("TEST Started Event", "Already started: must be hidden from browse.",
         "Test Hall", "Education", -5, "09:00", "10:00", 20, 1),
        ("TEST Full Event", "Capacity 2, both places taken.",
         "Test Hall", "Education", 5, "10:00", "11:00", 2, 1),
        ("TEST One Spot Left", "Capacity 2, one place taken (race-condition test).",
         "Test Hall", "Education", 6, "10:00", "11:00", 2, 2),
    ]
    for title, desc, loc, c, off, st, en, capy, creator in events:
        conn.execute(
            """INSERT INTO events (title, description, date, start_time, end_time,
                                   location, capacity, category_id, creator_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, desc, day(off), st, en, loc, capy, cat[c], creator))

    def event_id(title):
        return conn.execute("SELECT event_id FROM events WHERE title = ?", (title,)).fetchone()[0]

    full, one_left = event_id("TEST Full Event"), event_id("TEST One Spot Left")
    for uid in (1, 2):
        conn.execute("INSERT INTO rsvps (user_id, event_id) VALUES (?, ?)", (uid, full))
    conn.execute("INSERT INTO rsvps (user_id, event_id) VALUES (?, ?)", (1, one_left))


def seed_bulk(conn, n=500):
    rng = random.Random(42)
    cats = [r[0] for r in conn.execute("SELECT category_id FROM categories")]
    kinds = ["Meetup", "Workshop", "Festival", "Cleanup", "Tournament", "Class", "Night", "Walk"]
    topics = ["Park", "River", "Library", "Garden", "Chess", "Pottery", "Jazz", "Trivia", "Yoga", "Coding"]
    places = ["Central Park", "Waterfront Park", "Main Library", "Community Center", "Maple Hall", "Oak Street Field"]
    rows = []
    for i in range(n):
        h = rng.randint(8, 19)
        rows.append((f"{rng.choice(topics)} {rng.choice(kinds)} #{i}",
                     f"Bulk test event {i} about {rng.choice(topics).lower()}.",
                     day(rng.randint(1, 120)), f"{h:02d}:00", f"{h + 1:02d}:00",
                     rng.choice(places), rng.randint(10, 200),
                     rng.choice(cats), rng.randint(1, 2)))
    conn.executemany(
        """INSERT INTO events (title, description, date, start_time, end_time,
                               location, capacity, category_id, creator_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", rows)


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = get_connection()
    conn.execute("BEGIN")
    seed_core(conn)
    if "--bulk" in sys.argv:
        seed_bulk(conn)
    conn.execute("COMMIT")
    for t in ("users", "categories", "events", "rsvps", "favorites"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
    print("Seeded:", DB_PATH)
