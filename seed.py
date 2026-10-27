"""Fictitious demo data so the site doesn't look empty.

Run `python3 seed.py --reset` to wipe the local database and re-seed it.
Every demo account uses the password  demo-pass-123
"""
import sys
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

from werkzeug.security import generate_password_hash

DEMO_PASSWORD = "demo-pass-123"

# Background/text colors for the generated placeholder "photos", per category.
COLORS = {
    "Electronics": ("dbeafe", "1e3a8a"), "Keys": ("fef3c7", "92400e"),
    "ID / Cards": ("e0e7ff", "3730a3"), "Bags": ("dcfce7", "166534"),
    "Clothing": ("fce7f3", "9d174d"), "Water bottles": ("cffafe", "155e75"),
    "Books & notes": ("ffedd5", "9a3412"), "Jewelry": ("f3e8ff", "6b21a8"),
    "Other": ("e7e5e4", "44403c"),
}


def photo_url(title, category):
    bg, fg = COLORS[category]
    return f"https://placehold.co/640x480/{bg}/{fg}/png?font=raleway&text={quote_plus(title)}"

USERS = ["maria.lopez", "jchen", "priya_k", "sam.okafor", "lib_desk", "rec_center"]

# (poster, title, category, location, days ago, returned?, description)
ITEMS = [
    ("lib_desk", "Black AirPods Pro case", "Electronics", "Library, 2nd floor quiet room", 1, False,
     "Case only had the left earbud inside. Small scratch on the lid."),
    ("maria.lopez", "Blue Hydro Flask (32 oz)", "Water bottles", "Benson Center patio", 2, False,
     "Covered in stickers: a national parks one and a cat with sunglasses."),
    ("jchen", "Ring of 3 keys with a Totoro keychain", "Keys", "Parking structure, level 3", 2, False,
     "One looks like a car key (Honda), two small silver keys."),
    ("rec_center", "Grey Nike hoodie, size M", "Clothing", "Rec center, basketball court bleachers", 3, False,
     "Left after the evening pickup game."),
    ("priya_k", "TI-84 Plus graphing calculator", "Electronics", "Science building, room 104", 3, False,
     "Initials 'R.T.' scratched on the back."),
    ("lib_desk", "Student ID card — first name Daniel", "ID / Cards", "Library front desk", 4, False,
     "Bring another photo ID to pick it up at the front desk."),
    ("sam.okafor", "Green JanSport backpack", "Bags", "Bus stop by the main gate", 4, False,
     "Had a notebook and a phone charger inside. Turned in to Campus Safety."),
    ("maria.lopez", "Silver hoop earring", "Jewelry", "Women's restroom, Arts building", 5, False,
     "Just one earring, small and thin."),
    ("jchen", "Organic Chemistry textbook (Klein, 4th ed.)", "Books & notes", "Dining hall, table near the windows", 5, True,
     "Lots of highlighting in chapter 7."),
    ("rec_center", "Wireless Beats headphones (red)", "Electronics", "Rec center weight room", 6, False,
     "Found on the bench press. Battery is dead."),
    ("priya_k", "Spiral notebook, 'CS 110' on the cover", "Books & notes", "Engineering lab, 2nd floor", 6, False,
     "Lecture notes on recursion and linked lists. Someone will miss this before the midterm!"),
    ("lib_desk", "Prescription glasses, tortoiseshell frames", "Other", "Library study room 3B", 7, True,
     "In a black hard case."),
    ("sam.okafor", "Black umbrella with wooden handle", "Other", "Lecture hall A entrance", 7, False,
     "Large, golf-style umbrella."),
    ("maria.lopez", "Yellow rain jacket", "Clothing", "Mission gardens bench", 8, False,
     "Women's size S, had a hair tie in the pocket."),
    ("jchen", "MacBook charger (USB-C, 67W)", "Electronics", "Library 1st floor, outlet by the printers", 8, False,
     "Still plugged into the wall when I found it."),
    ("rec_center", "Brown leather wallet", "ID / Cards", "Rec center locker room", 9, True,
     "Contained a driver's license; owner was contacted and picked it up."),
    ("priya_k", "Blue and white scarf", "Clothing", "Campus coffee shop", 9, False,
     "Knitted, looks handmade."),
    ("lib_desk", "Kindle Paperwhite", "Electronics", "Library 3rd floor, carrel 42", 10, False,
     "Has a floral cover. Describe the lock screen to claim it."),
    ("sam.okafor", "Single car key fob (Toyota)", "Keys", "Soccer field sideline", 11, False,
     "No keyring, just the fob."),
    ("maria.lopez", "Pink Stanley tumbler", "Water bottles", "Business school lobby", 11, True,
     "40 oz with a straw."),
    ("jchen", "Black North Face fleece", "Clothing", "Dining hall coat rack", 12, False,
     "Men's L. Was hanging there for days."),
    ("rec_center", "Yoga mat (purple)", "Other", "Rec center studio B", 12, False,
     "Rolled up with a strap."),
    ("priya_k", "Gold necklace with a small cross", "Jewelry", "Chapel steps", 13, False,
     "Delicate chain; clasp seems broken."),
    ("lib_desk", "USB flash drive (SanDisk 64GB)", "Electronics", "Library computer lab, PC #17", 14, False,
     "Left in the computer. We didn't open any files."),
    ("sam.okafor", "Skateboard with red wheels", "Other", "Bike racks outside the residence halls", 14, True,
     "Deck has a mountain graphic."),
    ("maria.lopez", "Canvas tote bag with groceries", "Bags", "Shuttle stop, north campus", 15, False,
     "Had apples and a carton of oat milk (the milk has been tossed)."),
    ("jchen", "Apple Watch with black sport band", "Electronics", "Track around the football field", 16, False,
     "Found face-down on lane 2."),
    ("rec_center", "Swim goggles and cap", "Other", "Pool deck", 17, True,
     "Blue goggles, white cap."),
    ("priya_k", "Bike lock key on a carabiner", "Keys", "Bike racks by the library", 18, False,
     "Small Kryptonite key."),
    ("lib_desk", "Library book: 'Sapiens'", "Books & notes", "Student union lounge", 19, True,
     "Returned to the shelves — no owner needed!"),
    ("sam.okafor", "Denim jacket with pins", "Clothing", "Outdoor amphitheater", 20, False,
     "Pins include a frog, a rainbow, and a band logo."),
    ("maria.lopez", "Purple Samsung phone", "Electronics", "Arts building, ceramics studio", 21, True,
     "Owner called it while I was holding it. Reunited!"),
    ("jchen", "Black laptop sleeve (empty)", "Bags", "Engineering courtyard", 22, False,
     "13-inch size, has a luggage tag with no name."),
    ("rec_center", "Tennis racket (Wilson)", "Other", "Tennis courts", 24, False,
     "Grip tape is worn."),
    ("priya_k", "Parking permit hang tag", "ID / Cards", "Parking lot C", 26, True,
     "Turned in to Transportation Services."),
    ("lib_desk", "Reading glasses, red frames", "Other", "Library 2nd floor, couch", 28, False,
     "+1.5 strength printed on the arm."),
    ("sam.okafor", "Gym duffel bag", "Bags", "Rec center parking lot", 30, False,
     "Contains running shoes and a towel."),
    ("maria.lopez", "Engraved silver bracelet", "Jewelry", "Dining hall, near the dish return", 33, False,
     "Engraved with a date. Tell us the date to claim it."),
    ("jchen", "Graphing paper notebook and pencil case", "Books & notes", "Math building, room 210", 36, True,
     "Owner found via the class Discord."),
    ("rec_center", "Bluetooth speaker (JBL, blue)", "Electronics", "Sand volleyball court", 40, False,
     "Still works. Has some sand in it."),
]


def seed(conn):
    today = date.today()
    for i, username in enumerate(USERS):
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(DEMO_PASSWORD),
             (datetime.now() - timedelta(days=60 + i * 7)).isoformat(sep=" ", timespec="seconds")))
    ids = {r["username"]: r["id"] for r in conn.execute("SELECT id, username FROM users")}

    for poster, title, cat, where, days, returned, desc in ITEMS:
        found = today - timedelta(days=days)
        conn.execute(
            """INSERT INTO items (user_id, title, description, category, location, found_date,
                                  photo_url, status, created_at, returned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ids[poster], title, desc, cat, where, found.isoformat(),
             photo_url(title, cat),
             "returned" if returned else "unclaimed",
             f"{found.isoformat()} 12:00:00",
             (found + timedelta(days=2)).isoformat() + " 15:00:00" if returned else None))


if __name__ == "__main__":
    import os
    import db

    path = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__),
                                                         "instance", "lostfound.db"))
    if "--reset" in sys.argv and os.path.exists(path):
        os.remove(path)
    db.init_db(path)
    print(f"Database ready at {path}")
