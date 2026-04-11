import streamlit as st
import sqlite3
import pandas as pd
import random
import os
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ─────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────
st.set_page_config(
    page_title="SkyBook | Airline Reservation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* ── HERO HEADER ── */
.hero {
    text-align: center;
    padding: 2rem 0 1rem;
}
.hero h1 {
    font-size: 3.2rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -1px;
    margin: 0;
}
.hero h1 span { color: #f9a826; }
.hero p { color: #aaa; font-size: 1rem; margin-top: 0.3rem; }

/* ── CARD ── */
.card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(249,168,38,0.15);
}
.card-title { font-size: 1.15rem; font-weight: 700; color: #f9a826; margin-bottom: 0.3rem; }
.card-route { font-size: 1.4rem; font-weight: 800; color: #fff; }
.card-meta  { font-size: 0.85rem; color: #bbb; margin-top: 0.25rem; }
.card-price { font-size: 1.6rem; font-weight: 800; color: #4ade80; }
.badge {
    display: inline-block;
    background: rgba(249,168,38,0.2);
    color: #f9a826;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid #f9a826;
    margin-right: 6px;
}

/* ── STEPS ── */
.step-bar { display: flex; justify-content: center; gap: 0; margin: 1.5rem 0; }
.step {
    padding: 8px 24px;
    background: rgba(255,255,255,0.05);
    color: #666;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.08);
}
.step:first-child { border-radius: 8px 0 0 8px; }
.step:last-child  { border-radius: 0 8px 8px 0; }
.step.active { background: #f9a826; color: #0f0c29; border-color: #f9a826; }
.step.done   { background: rgba(74,222,128,0.15); color: #4ade80; border-color: #4ade80; }

/* ── INPUTS ── */
.stTextInput > div > input,
.stNumberInput > div > input,
.stDateInput > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Sora', sans-serif !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
}
label { color: #ccc !important; font-size: 0.85rem !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #f9a826, #f97316) !important;
    color: #0f0c29 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.5rem 1.5rem !important;
    font-family: 'Sora', sans-serif !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: rgba(15,12,41,0.9) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── SUCCESS / ERROR ── */
.stSuccess { background: rgba(74,222,128,0.1) !important; border-color: #4ade80 !important; }
.stError   { background: rgba(239,68,68,0.1) !important; border-color: #ef4444 !important; }

hr { border-color: rgba(255,255,255,0.08) !important; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SQLITE DB SETUP
# ─────────────────────────────────────────
DB_PATH = "skybook.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        username   TEXT NOT NULL UNIQUE,
        email      TEXT NOT NULL UNIQUE,
        password   TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS airports (
        airport_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        city         TEXT NOT NULL UNIQUE,
        airport_name TEXT NOT NULL,
        iata_code    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS flights (
        flight_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_name  TEXT NOT NULL,
        source       TEXT NOT NULL,
        destination  TEXT NOT NULL,
        dep_time     TEXT NOT NULL,
        arr_time     TEXT NOT NULL,
        price        REAL NOT NULL,
        total_seats  INTEGER NOT NULL DEFAULT 120,
        is_active    INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (source)      REFERENCES airports(city),
        FOREIGN KEY (destination) REFERENCES airports(city)
    );

    CREATE TABLE IF NOT EXISTS bookings (
        booking_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        flight_id    INTEGER NOT NULL,
        travel_date  TEXT NOT NULL,
        total_amount REAL NOT NULL,
        booked_at    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id)   REFERENCES users(user_id),
        FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
    );

    CREATE TABLE IF NOT EXISTS passengers (
        passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id   INTEGER NOT NULL,
        name         TEXT NOT NULL,
        age          INTEGER NOT NULL,
        gender       TEXT NOT NULL,
        seat_no      TEXT NOT NULL,
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id     INTEGER NOT NULL UNIQUE,
        payment_method TEXT NOT NULL,
        amount         REAL NOT NULL,
        payment_status TEXT NOT NULL DEFAULT 'Pending',
        paid_at        TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
    );
    """)
    conn.commit()

    # Seed airports if empty
    if c.execute("SELECT COUNT(*) FROM airports").fetchone()[0] == 0:
        airports = [
            ('Delhi',       'Indira Gandhi International Airport',                  'DEL'),
            ('Mumbai',      'Chhatrapati Shivaji Maharaj International Airport',    'BOM'),
            ('Bangalore',   'Kempegowda International Airport',                     'BLR'),
            ('Hyderabad',   'Rajiv Gandhi International Airport',                   'HYD'),
            ('Chennai',     'Chennai International Airport',                        'MAA'),
            ('Kolkata',     'Netaji Subhas Chandra Bose International Airport',     'CCU'),
            ('Pune',        'Pune Airport',                                         'PNQ'),
            ('Ahmedabad',   'Sardar Vallabhbhai Patel International Airport',       'AMD'),
            ('Jaipur',      'Jaipur International Airport',                         'JAI'),
            ('Kochi',       'Cochin International Airport',                         'COK'),
            ('Goa',         'Goa International Airport',                            'GOI'),
            ('Lucknow',     'Chaudhary Charan Singh International Airport',         'LKO'),
            ('Chandigarh',  'Chandigarh International Airport',                     'IXC'),
            ('Nagpur',      'Dr. Babasaheb Ambedkar International Airport',         'NAG'),
            ('Srinagar',    'Sheikh ul-Alam International Airport',                 'SXR'),
        ]
        c.executemany("INSERT OR IGNORE INTO airports(city,airport_name,iata_code) VALUES(?,?,?)", airports)
        conn.commit()

    # Seed demo user if not exists
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO users(username,email,password) VALUES(?,?,?)",
                  ('demo', 'demo@skybook.in', 'demo123'))
        conn.commit()

    # Seed flights if empty
    if c.execute("SELECT COUNT(*) FROM flights").fetchone()[0] == 0:
        seed_flights(c)
        conn.commit()

    conn.close()


def seed_flights(c):
    """Generate flights for all city pairs (3 per route)."""
    cities = [
        'Delhi','Mumbai','Bangalore','Hyderabad','Chennai',
        'Kolkata','Pune','Ahmedabad','Jaipur','Kochi',
        'Goa','Lucknow','Chandigarh','Nagpur','Srinagar'
    ]
    airlines = [
        ("IndiGo 6E",    "06:00", 0.92),
        ("Air India AI", "12:30", 1.15),
        ("SpiceJet SG",  "18:00", 0.92),
    ]
    # Base prices between city pairs (distance-based approximation)
    base_prices = {
        ('Delhi','Mumbai'):900, ('Delhi','Bangalore'):1300, ('Delhi','Hyderabad'):1000,
        ('Delhi','Chennai'):1350, ('Delhi','Kolkata'):1100, ('Delhi','Pune'):950,
        ('Delhi','Ahmedabad'):650, ('Delhi','Jaipur'):250, ('Delhi','Kochi'):1600,
        ('Delhi','Goa'):1200, ('Delhi','Lucknow'):400, ('Delhi','Chandigarh'):250,
        ('Delhi','Nagpur'):700, ('Delhi','Srinagar'):550,
        ('Mumbai','Bangalore'):700, ('Mumbai','Hyderabad'):550, ('Mumbai','Chennai'):850,
        ('Mumbai','Kolkata'):1400, ('Mumbai','Pune'):250, ('Mumbai','Ahmedabad'):380,
        ('Mumbai','Jaipur'):780, ('Mumbai','Kochi'):900, ('Mumbai','Goa'):380,
        ('Mumbai','Lucknow'):1050, ('Mumbai','Chandigarh'):1150, ('Mumbai','Nagpur'):620,
        ('Mumbai','Srinagar'):1400,
        ('Bangalore','Hyderabad'):450, ('Bangalore','Chennai'):280, ('Bangalore','Kolkata'):1280,
        ('Bangalore','Pune'):650, ('Bangalore','Ahmedabad'):1050, ('Bangalore','Jaipur'):1300,
        ('Bangalore','Kochi'):320, ('Bangalore','Goa'):450, ('Bangalore','Lucknow'):1320,
        ('Bangalore','Chandigarh'):1650, ('Bangalore','Nagpur'):780, ('Bangalore','Srinagar'):1980,
        ('Hyderabad','Chennai'):450, ('Hyderabad','Kolkata'):1050, ('Hyderabad','Pune'):480,
        ('Hyderabad','Ahmedabad'):780, ('Hyderabad','Jaipur'):940, ('Hyderabad','Kochi'):750,
        ('Hyderabad','Goa'):500, ('Hyderabad','Lucknow'):920, ('Hyderabad','Chandigarh'):1260,
        ('Hyderabad','Nagpur'):380, ('Hyderabad','Srinagar'):1580,
        ('Chennai','Kolkata'):1150, ('Chennai','Pune'):800, ('Chennai','Ahmedabad'):1180,
        ('Chennai','Jaipur'):1360, ('Chennai','Kochi'):500, ('Chennai','Goa'):660,
        ('Chennai','Lucknow'):1280, ('Chennai','Chandigarh'):1680, ('Chennai','Nagpur'):760,
        ('Chennai','Srinagar'):2020,
        ('Kolkata','Pune'):1400, ('Kolkata','Ahmedabad'):1480, ('Kolkata','Jaipur'):1260,
        ('Kolkata','Kochi'):1640, ('Kolkata','Goa'):1520, ('Kolkata','Lucknow'):820,
        ('Kolkata','Chandigarh'):1340, ('Kolkata','Nagpur'):900, ('Kolkata','Srinagar'):1660,
        ('Pune','Ahmedabad'):480, ('Pune','Jaipur'):840, ('Pune','Kochi'):860,
        ('Pune','Goa'):300, ('Pune','Lucknow'):1050, ('Pune','Chandigarh'):1200,
        ('Pune','Nagpur'):560, ('Pune','Srinagar'):1460,
        ('Ahmedabad','Jaipur'):500, ('Ahmedabad','Kochi'):1280, ('Ahmedabad','Goa'):720,
        ('Ahmedabad','Lucknow'):880, ('Ahmedabad','Chandigarh'):840, ('Ahmedabad','Nagpur'):650,
        ('Ahmedabad','Srinagar'):1060,
        ('Jaipur','Kochi'):1580, ('Jaipur','Goa'):1100, ('Jaipur','Lucknow'):500,
        ('Jaipur','Chandigarh'):400, ('Jaipur','Nagpur'):660, ('Jaipur','Srinagar'):700,
        ('Kochi','Goa'):600, ('Kochi','Lucknow'):1620, ('Kochi','Chandigarh'):1920,
        ('Kochi','Nagpur'):1100, ('Kochi','Srinagar'):2220,
        ('Goa','Lucknow'):1260, ('Goa','Chandigarh'):1460, ('Goa','Nagpur'):740,
        ('Goa','Srinagar'):1740,
        ('Lucknow','Chandigarh'):560, ('Lucknow','Nagpur'):580, ('Lucknow','Srinagar'):920,
        ('Chandigarh','Nagpur'):960, ('Chandigarh','Srinagar'):400,
        ('Nagpur','Srinagar'):1320,
    }
    # Duration in minutes (approximate)
    durations = {
        ('Delhi','Mumbai'):126, ('Delhi','Bangalore'):176, ('Delhi','Hyderabad'):135,
        ('Delhi','Chennai'):177, ('Delhi','Kolkata'):148, ('Delhi','Pune'):128,
        ('Delhi','Ahmedabad'):97, ('Delhi','Jaipur'):50, ('Delhi','Kochi'):203,
        ('Delhi','Goa'):155, ('Delhi','Lucknow'):69, ('Delhi','Chandigarh'):48,
        ('Delhi','Nagpur'):102, ('Delhi','Srinagar'):84,
        ('Mumbai','Bangalore'):101, ('Mumbai','Hyderabad'):84, ('Mumbai','Chennai'):118,
        ('Mumbai','Kolkata'):176, ('Mumbai','Pune'):40, ('Mumbai','Ahmedabad'):66,
        ('Mumbai','Jaipur'):106, ('Mumbai','Kochi'):119, ('Mumbai','Goa'):64,
        ('Mumbai','Lucknow'):132, ('Mumbai','Chandigarh'):143, ('Mumbai','Nagpur'):90,
        ('Mumbai','Srinagar'):169,
        ('Bangalore','Hyderabad'):72, ('Bangalore','Chennai'):55, ('Bangalore','Kolkata'):164,
        ('Bangalore','Pune'):92, ('Bangalore','Ahmedabad'):134, ('Bangalore','Jaipur'):160,
        ('Bangalore','Kochi'):59, ('Bangalore','Goa'):72, ('Bangalore','Lucknow'):162,
        ('Bangalore','Chandigarh'):194, ('Bangalore','Nagpur'):107, ('Bangalore','Srinagar'):227,
        ('Hyderabad','Chennai'):73, ('Hyderabad','Kolkata'):133, ('Hyderabad','Pune'):73,
        ('Hyderabad','Ahmedabad'):105, ('Hyderabad','Jaipur'):121, ('Hyderabad','Kochi'):101,
        ('Hyderabad','Goa'):76, ('Hyderabad','Lucknow'):119, ('Hyderabad','Chandigarh'):154,
        ('Hyderabad','Nagpur'):64, ('Hyderabad','Srinagar'):188,
        ('Chennai','Kolkata'):145, ('Chennai','Pune'):107, ('Chennai','Ahmedabad'):146,
        ('Chennai','Jaipur'):164, ('Chennai','Kochi'):76, ('Chennai','Goa'):94,
        ('Chennai','Lucknow'):156, ('Chennai','Chandigarh'):195, ('Chennai','Nagpur'):104,
        ('Chennai','Srinagar'):230,
        ('Kolkata','Pune'):169, ('Kolkata','Ahmedabad'):176, ('Kolkata','Jaipur'):153,
        ('Kolkata','Kochi'):221, ('Kolkata','Goa'):180, ('Kolkata','Lucknow'):109,
        ('Kolkata','Chandigarh'):160, ('Kolkata','Nagpur'):117, ('Kolkata','Srinagar'):194,
        ('Pune','Ahmedabad'):73, ('Pune','Jaipur'):109, ('Pune','Kochi'):111,
        ('Pune','Goa'):57, ('Pune','Lucknow'):130, ('Pune','Chandigarh'):145,
        ('Pune','Nagpur'):83, ('Pune','Srinagar'):174,
        ('Ahmedabad','Jaipur'):76, ('Ahmedabad','Kochi'):155, ('Ahmedabad','Goa'):100,
        ('Ahmedabad','Lucknow'):114, ('Ahmedabad','Chandigarh'):111, ('Ahmedabad','Nagpur'):92,
        ('Ahmedabad','Srinagar'):134,
        ('Jaipur','Kochi'):186, ('Jaipur','Goa'):137, ('Jaipur','Lucknow'):77,
        ('Jaipur','Chandigarh'):66, ('Jaipur','Nagpur'):91, ('Jaipur','Srinagar'):97,
        ('Kochi','Goa'):85, ('Kochi','Lucknow'):221, ('Kochi','Chandigarh'):251,
        ('Kochi','Nagpur'):135, ('Kochi','Srinagar'):253,
        ('Goa','Lucknow'):153, ('Goa','Chandigarh'):173, ('Goa','Nagpur'):101,
        ('Goa','Srinagar'):202,
        ('Lucknow','Chandigarh'):82, ('Lucknow','Nagpur'):85, ('Lucknow','Srinagar'):117,
        ('Chandigarh','Nagpur'):121, ('Chandigarh','Srinagar'):66,
        ('Nagpur','Srinagar'):156,
    }

    flight_num = 100
    rows = []
    for src in cities:
        for dst in cities:
            if src == dst:
                continue
            key = (src, dst) if (src, dst) in base_prices else (dst, src)
            base = base_prices.get(key, 1000)
            dur  = durations.get(key, durations.get((dst, src), 120))
            for airline_name, dep_str, price_mult in airlines:
                dep_h, dep_m = map(int, dep_str.split(":"))
                dep_mins = dep_h * 60 + dep_m
                arr_mins = dep_mins + dur
                arr_h = (arr_mins // 60) % 24
                arr_m = arr_mins % 60
                dep_time = f"{dep_h:02d}:{dep_m:02d}:00"
                arr_time = f"{arr_h:02d}:{arr_m:02d}:00"
                price = round(base * price_mult * 6.5 / 10) * 10  # scale to INR-ish
                flight_name = f"{airline_name}-{flight_num}"
                rows.append((flight_name, src, dst, dep_time, arr_time, price))
                flight_num += 1

    c.executemany(
        "INSERT INTO flights(flight_name,source,destination,dep_time,arr_time,price) VALUES(?,?,?,?,?,?)",
        rows
    )


# ─────────────────────────────────────────
# DB HELPER
# ─────────────────────────────────────────
def run(sql, params=(), fetch=True):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            rows = cur.fetchall()
            conn.close()
            return [tuple(r) for r in rows]
        else:
            conn.commit()
            last_id = cur.lastrowid
            conn.close()
            return last_id
    except Exception as e:
        st.error(f"DB error: {e}")
        return [] if fetch else None


# ─────────────────────────────────────────
# INIT DB ON FIRST RUN
# ─────────────────────────────────────────
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True


# ─────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────
defaults = {
    "user": None,
    "step": "search",
    "chosen_flight": None,
    "travel_date": None,
    "n_pax": 1,
    "pax_details": [],
    "selected_seats": [],
    "booking_id": None,
    "total": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────
# HERO
# ─────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>✈ Sky<span>Book</span></h1>
  <p>Fast · Affordable · Hassle-free flights across India</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SIDEBAR – Auth
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Account")
    menu = st.selectbox("", ["Login", "Register", "Admin"], label_visibility="collapsed")

    if menu == "Register":
        with st.form("reg_form"):
            un = st.text_input("Username")
            em = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Create Account"):
                existing = run("SELECT user_id FROM users WHERE username=?", (un,))
                if existing:
                    st.error("Username already taken.")
                else:
                    run("INSERT INTO users(username,email,password) VALUES(?,?,?)",
                        (un, em, pw), fetch=False)
                    st.success("Account created! Please login.")

    elif menu == "Login":
        if st.session_state.user is None:
            with st.form("login_form"):
                un = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    rows = run("SELECT * FROM users WHERE username=? AND password=?", (un, pw))
                    if rows:
                        st.session_state.user = rows[0]
                        st.session_state.step = "search"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            st.markdown("---")
            st.markdown("**Demo:** username `demo` / password `demo123`")
        else:
            st.success(f"👋 {st.session_state.user[1]}")

            # My Bookings
            st.markdown("---")
            st.markdown("#### 🎫 My Bookings")
            my_bookings = run("""
                SELECT b.booking_id, f.flight_name, f.source, f.destination,
                       b.travel_date, b.total_amount, p.payment_status
                FROM bookings b
                JOIN flights f ON b.flight_id=f.flight_id
                LEFT JOIN payments p ON b.booking_id=p.booking_id
                WHERE b.user_id=?
                ORDER BY b.booking_id DESC
                LIMIT 5
            """, (st.session_state.user[0],))
            if my_bookings:
                for bk in my_bookings:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.04);border-radius:8px;
                                padding:8px 12px;margin-bottom:6px;font-size:0.78rem;">
                      <b style="color:#f9a826">#{bk[0]}</b> · {bk[2]} → {bk[3]}<br>
                      <span style="color:#aaa">{bk[4]} · ₹{bk[5]:,.0f}</span>
                      &nbsp;<span style="color:#4ade80">{bk[6] or 'Pending'}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No bookings yet.")

            st.markdown("---")
            if st.button("Logout"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

    elif menu == "Admin":
        ap = st.text_input("Admin Password", type="password")
        if ap == "admin123":
            st.markdown("---")
            rows = run("""
                SELECT u.username, f.flight_name, f.source, f.destination,
                       b.travel_date, b.total_amount
                FROM bookings b
                JOIN users u ON b.user_id=u.user_id
                JOIN flights f ON b.flight_id=f.flight_id
                ORDER BY b.booking_id DESC
            """)
            if rows:
                df = pd.DataFrame(rows, columns=["User","Flight","From","To","Date","₹ Amount"])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No bookings yet.")


# ─────────────────────────────────────────
# MAIN CONTENT – requires login
# ─────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("""
    <div class="card" style="text-align:center;padding:3rem;">
      <div style="font-size:3rem;">🛫</div>
      <h3 style="color:white;">Please login to search & book flights</h3>
      <p style="color:#aaa;">Use the sidebar → Login to get started<br>
      <b style="color:#f9a826">Demo credentials: demo / demo123</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─── STEP BAR ────────────────────────────
step_labels = ["🔍 Search", "💺 Seats", "💳 Payment", "✅ Done"]
step_keys   = ["search", "seats", "payment", "done"]
bar_html = '<div class="step-bar">'
for i, (lbl, key) in enumerate(zip(step_labels, step_keys)):
    cls = "active" if key == st.session_state.step else (
          "done"   if step_keys.index(st.session_state.step) > i else "")
    bar_html += f'<div class="step {cls}">{lbl}</div>'
bar_html += "</div>"
st.markdown(bar_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# STEP 1 – SEARCH
# ═══════════════════════════════════════════
if st.session_state.step == "search":
    cities = [r[0] for r in run("SELECT city FROM airports ORDER BY city")]

    with st.container():
        col1, col2, col3, col4 = st.columns([2,2,2,1])
        with col1:
            src = st.selectbox("From 🛫", cities, key="src_city")
        with col2:
            dsts = [c for c in cities if c != src]
            dst = st.selectbox("To 🛬", dsts, key="dst_city")
        with col3:
            tdate = st.date_input("Travel Date 📅",
                                  min_value=datetime.today().date(),
                                  key="tdate_input")
        with col4:
            n_pax = st.number_input("Passengers", 1, 6, 1, key="npax_input")

        search_btn = st.button("🔍  Search Flights", use_container_width=True)

    if search_btn:
        if src == dst:
            st.error("Source and destination cannot be the same!")
        else:
            rows = run(
                "SELECT * FROM flights WHERE source=? AND destination=? AND is_active=1",
                (src, dst)
            )
            if not rows:
                st.warning("No flights found for this route.")
            else:
                st.session_state["flight_results"] = rows
                st.session_state["search_src"]   = src
                st.session_state["search_dst"]   = dst
                st.session_state["search_date"]  = tdate
                st.session_state["search_npax"]  = n_pax

    # Show results
    if st.session_state.get("flight_results"):
        st.markdown("---")
        st.markdown(f"### Available Flights · {st.session_state.search_src} → {st.session_state.search_dst}")

        for f in st.session_state.flight_results[:8]:
            dep = str(f[4])[:5]
            arr = str(f[5])[:5]
            try:
                d1 = datetime.strptime(dep, "%H:%M")
                d2 = datetime.strptime(arr, "%H:%M")
                diff = int((d2 - d1).total_seconds() // 60)
                if diff < 0:
                    diff += 24 * 60
                dur = f"{diff//60}h {diff%60}m"
            except:
                dur = "–"

            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div class="card">
                  <div class="card-title">✈ {f[1]}</div>
                  <div class="card-route">{f[2]} &nbsp;→&nbsp; {f[3]}</div>
                  <div class="card-meta">
                    🕐 Dep: <b style="color:#fff">{dep}</b> &nbsp;·&nbsp;
                    🕑 Arr: <b style="color:#fff">{arr}</b> &nbsp;·&nbsp;
                    ⏱ {dur}
                    &nbsp;&nbsp;
                    <span class="badge">Economy</span>
                    <span class="badge">Wi-Fi</span>
                  </div>
                  <div class="card-price" style="margin-top:0.5rem;">₹{f[6]:,.0f}
                    <span style="font-size:0.85rem;color:#aaa;">/ person</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("Book →", key=f"book_{f[0]}"):
                    st.session_state.chosen_flight  = f
                    st.session_state.travel_date    = st.session_state.search_date
                    st.session_state.n_pax          = st.session_state.search_npax
                    st.session_state.selected_seats = []
                    st.session_state.pax_details    = []
                    st.session_state.step           = "seats"
                    st.rerun()


# ═══════════════════════════════════════════
# STEP 2 – SEATS & PASSENGER DETAILS
# ═══════════════════════════════════════════
elif st.session_state.step == "seats":
    f   = st.session_state.chosen_flight
    n   = st.session_state.n_pax
    dep = str(f[4])[:5]
    arr = str(f[5])[:5]

    st.markdown(f"""
    <div class="card">
      <div class="card-title">✈ {f[1]}</div>
      <div class="card-route">{f[2]} → {f[3]}</div>
      <div class="card-meta">🗓 {st.session_state.travel_date} &nbsp;·&nbsp;
        🕐 {dep} → {arr} &nbsp;·&nbsp; {n} passenger(s)</div>
      <div class="card-price">Total: ₹{f[6]*n:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SEAT MAP ────────────────────────────
    st.markdown("### 💺 Choose Your Seats")
    st.caption(f"Select exactly {n} seat(s).")

    rng = random.Random(f[0])
    COLS = ["A","B","C","D","E","F"]
    ROWS = 20
    occupied = set(
        f"{rng.randint(1,ROWS)}{rng.choice(COLS)}"
        for _ in range(30)
    )

    # Build visual seat map
    col_header = '<div style="display:flex;gap:6px;margin-bottom:4px;align-items:center;">'
    col_header += '<div style="width:24px;"></div>'
    for col in COLS:
        if col == "D":
            col_header += '<div style="width:16px;"></div>'
        col_header += f'<div style="width:36px;text-align:center;color:#64748b;font-size:0.7rem;">{col}</div>'
    col_header += "</div>"

    seat_html = f'<div style="display:flex;flex-direction:column;gap:6px;align-items:flex-start;margin:1rem 0;">{col_header}'
    for row in range(1, ROWS+1):
        seat_html += '<div style="display:flex;gap:6px;align-items:center;">'
        seat_html += f'<div style="width:24px;color:#aaa;font-size:0.75rem;text-align:center;font-family:monospace;">{row}</div>'
        for col in COLS:
            if col == "D":
                seat_html += '<div style="width:16px;"></div>'
            seat = f"{row}{col}"
            if seat in occupied:
                bg, color, cursor = "#374151", "#4b5563", "not-allowed"
                opacity = "0.5"
            elif seat in st.session_state.get("selected_seats", []):
                bg, color, cursor = "#f9a826", "#0f0c29", "pointer"
                opacity = "1"
            else:
                bg, color, cursor = "#334155", "#94a3b8", "pointer"
                opacity = "1"
            seat_html += f'<div style="width:36px;height:36px;background:{bg};color:{color};border-radius:8px 8px 4px 4px;display:flex;align-items:center;justify-content:center;font-size:0.58rem;font-weight:700;cursor:{cursor};opacity:{opacity};font-family:monospace;">{seat}</div>'
        seat_html += "</div>"
    seat_html += "</div>"

    st.markdown(seat_html, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;gap:16px;margin:0.5rem 0 1rem;font-size:0.8rem;color:#aaa;">
      <span><span style="background:#334155;padding:2px 8px;border-radius:4px;">&nbsp;</span> Available</span>
      <span><span style="background:#f9a826;padding:2px 8px;border-radius:4px;">&nbsp;</span> Selected</span>
      <span style="opacity:0.5"><span style="background:#374151;padding:2px 8px;border-radius:4px;">&nbsp;</span> Taken</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Type seat numbers to select** (e.g. `3A`, `5C`) — need exactly {n}")
    seat_input = st.text_input(
        "Seats",
        value=", ".join(st.session_state.selected_seats),
        placeholder="e.g. 3A, 7C",
        label_visibility="collapsed"
    )
    if st.button("✔ Confirm Seats"):
        raw   = [s.strip().upper() for s in seat_input.split(",") if s.strip()]
        valid = [s for s in raw if
                 len(s) >= 2 and
                 s[:-1].isdigit() and
                 1 <= int(s[:-1]) <= ROWS and
                 s[-1] in COLS and
                 s not in occupied]
        unique = list(dict.fromkeys(valid))
        if len(unique) != n:
            st.error(f"Please select exactly {n} valid, available seat(s). Got {len(unique)}.")
        else:
            st.session_state.selected_seats = unique
            st.success(f"Seats confirmed: {', '.join(unique)}")

    # ── PASSENGER DETAILS ────────────────────
    if len(st.session_state.selected_seats) == n:
        st.markdown("### 👤 Passenger Details")
        pax_list  = []
        all_filled = True
        for i in range(n):
            with st.expander(f"Passenger {i+1} – Seat {st.session_state.selected_seats[i]}", expanded=True):
                c1, c2, c3 = st.columns(3)
                nm  = c1.text_input("Full Name", key=f"pname_{i}")
                age = c2.number_input("Age", 1, 100, key=f"page_{i}")
                gen = c3.selectbox("Gender", ["Male","Female","Other"], key=f"pgen_{i}")
                if not nm.strip():
                    all_filled = False
                pax_list.append({
                    "name": nm, "age": age, "gender": gen,
                    "seat": st.session_state.selected_seats[i]
                })

        if all_filled:
            st.session_state.pax_details = pax_list
            col_back, col_next = st.columns([1,3])
            with col_back:
                if st.button("← Back"):
                    st.session_state.step = "search"
                    st.rerun()
            with col_next:
                if st.button("Proceed to Payment →", use_container_width=True):
                    st.session_state.step = "payment"
                    st.rerun()
        else:
            st.info("Fill in all passenger names to continue.")


# ═══════════════════════════════════════════
# STEP 3 – PAYMENT
# ═══════════════════════════════════════════
elif st.session_state.step == "payment":
    import time

    f     = st.session_state.chosen_flight
    n     = st.session_state.n_pax
    total = f[6] * n
    pax   = st.session_state.pax_details
    tdate = st.session_state.travel_date

    st.markdown("### 🧾 Booking Summary")
    pax_html = "".join(
        f"<tr><td style='color:#ccc;padding:4px 12px'>{i+1}. {p['name']}</td>"
        f"<td style='color:#aaa;padding:4px 12px'>Age {p['age']}, {p['gender']}</td>"
        f"<td style='color:#f9a826;padding:4px 12px'>Seat {p['seat']}</td></tr>"
        for i, p in enumerate(pax)
    )
    st.markdown(f"""
    <div class="card">
      <div class="card-title">✈ {f[1]}</div>
      <div class="card-route">{f[2]} → {f[3]}</div>
      <div class="card-meta">🗓 {tdate} &nbsp;·&nbsp; Dep {str(f[4])[:5]} → Arr {str(f[5])[:5]}</div>
      <table style="width:100%;margin-top:1rem;border-collapse:collapse;">{pax_html}</table>
      <hr style="margin:1rem 0;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="color:#aaa;">Base fare × {n} + taxes</span>
        <div class="card-price">₹{total:,.0f}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💳 Payment Method")
    method = st.radio("", ["UPI", "Credit / Debit Card", "Net Banking", "Wallet"],
                      horizontal=True, label_visibility="collapsed")

    if method == "UPI":
        st.text_input("UPI ID", placeholder="yourname@upi", key="upi_id")
        st.markdown('<div style="color:#64748b;font-size:0.75rem;">Demo mode — no real transaction</div>', unsafe_allow_html=True)

    elif method == "Credit / Debit Card":
        c1, c2 = st.columns(2)
        c1.text_input("Card Number", value="4111 1111 1111 1111", key="card_num")
        c2.text_input("Name on Card", placeholder="As on card", key="card_name")
        c3, c4 = st.columns(2)
        c3.text_input("Expiry", value="12/26", key="card_exp")
        c4.text_input("CVV", value="123", type="password", key="card_cvv")
        st.markdown('<div style="color:#64748b;font-size:0.75rem;">🔒 Demo card — no real charge</div>', unsafe_allow_html=True)

    elif method == "Net Banking":
        bank = st.selectbox("Select Your Bank", ["SBI","HDFC","ICICI","Axis","Kotak","PNB","BOB"])
        st.markdown(f'<div style="color:#64748b;font-size:0.75rem;">Demo only — redirecting to {bank} portal (no redirect happens)</div>', unsafe_allow_html=True)

    else:
        st.text_input("Wallet / Phone Number", value="9876543210", key="wallet_ph")
        st.markdown('<div style="color:#4ade80;font-size:0.8rem;">✅ Wallet Balance: ₹50,000 (Demo)</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_pay = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            st.session_state.step = "seats"
            st.rerun()
    with col_pay:
        pay_btn = st.button(f"💰  Pay ₹{total:,.0f} Now", use_container_width=True)

    if pay_btn:
        status_box = st.empty()
        for msg, icon in [
            ("Contacting payment gateway…", "🔄"),
            ("Verifying your details…", "🔐"),
            ("Processing payment…", "💸"),
        ]:
            status_box.markdown(f"""
            <div class="card" style="text-align:center;padding:1.5rem;">
              <div style="font-size:2rem;">{icon}</div>
              <div style="color:#f9a826;font-weight:700;margin-top:0.5rem;">{msg}</div>
            </div>""", unsafe_allow_html=True)
            time.sleep(1)

        fake_txn = f"TXN{''.join([str(random.randint(0,9)) for _ in range(12)])}"
        status_box.markdown(f"""
        <div class="card" style="text-align:center;padding:1.5rem;border-color:rgba(74,222,128,0.4);">
          <div style="font-size:2.5rem;">✅</div>
          <div style="color:#4ade80;font-weight:800;font-size:1.2rem;margin-top:0.5rem;">Payment Successful!</div>
          <div style="color:#aaa;font-size:0.8rem;margin-top:0.4rem;">
            Transaction ID: <b style="color:#f9a826;">{fake_txn}</b>
          </div>
        </div>""", unsafe_allow_html=True)
        time.sleep(0.8)

        booking_id = run(
            "INSERT INTO bookings(user_id,flight_id,travel_date,total_amount) VALUES(?,?,?,?)",
            (st.session_state.user[0], f[0], str(tdate), total), fetch=False
        )
        if booking_id:
            for p in pax:
                run(
                    "INSERT INTO passengers(booking_id,name,age,gender,seat_no) VALUES(?,?,?,?,?)",
                    (booking_id, p["name"], p["age"], p["gender"], p["seat"]), fetch=False
                )
            run(
                "INSERT INTO payments(booking_id,payment_method,amount,payment_status) VALUES(?,?,?,?)",
                (booking_id, method, total, "Success"), fetch=False
            )
            st.session_state.booking_id = booking_id
            st.session_state.total      = total
            st.session_state.step       = "done"
            st.rerun()


# ═══════════════════════════════════════════
# STEP 4 – CONFIRMATION + PDF TICKET
# ═══════════════════════════════════════════
elif st.session_state.step == "done":
    f          = st.session_state.chosen_flight
    pax        = st.session_state.pax_details
    tdate      = st.session_state.travel_date
    total      = st.session_state.total
    booking_id = st.session_state.booking_id

    st.balloons()
    st.markdown(f"""
    <div class="card" style="text-align:center;padding:2rem;">
      <div style="font-size:3.5rem;">🎉</div>
      <h2 style="color:#4ade80;margin:0.5rem 0;">Booking Confirmed!</h2>
      <p style="color:#aaa;">Booking ID: <b style="color:#f9a826;">#{booking_id}</b></p>
    </div>
    """, unsafe_allow_html=True)

    def make_ticket_pdf(booking_id, flight, pax_list, travel_date, total):
        buf = BytesIO()
        c   = canvas.Canvas(buf, pagesize=A4)
        W, H = A4

        c.setFillColor(colors.HexColor("#0f0c29"))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#f9a826"))
        c.rect(0, H-100, W, 100, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#0f0c29"))
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(W/2, H-55, "SkyBook  |  BOARDING PASS")
        c.setFont("Helvetica", 11)
        c.drawCentredString(W/2, H-78, "Airline Reservation System")

        c.setFillColor(colors.HexColor("#1e1b4b"))
        c.roundRect(30, H-260, W-60, 145, 12, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#f9a826"))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, H-140, str(flight[1]))

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 30)
        c.drawString(50, H-185, str(flight[2]))
        c.drawString(W-160, H-185, str(flight[3]))
        c.setFont("Helvetica", 13)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawCentredString(W/2, H-185, "-------- -> --------")
        c.drawCentredString(W/2, H-205, f"Dep: {str(flight[4])[:5]}  |  Arr: {str(flight[5])[:5]}")

        c.setFillColor(colors.HexColor("#f9a826"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, H-235, f"Date: {travel_date}")
        c.drawRightString(W-50, H-235, f"Booking ID: #{booking_id}")

        c.setFillColor(colors.HexColor("#1e1b4b"))
        c.roundRect(30, H-460, W-60, 185, 12, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#f9a826"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, H-285, "PASSENGERS")

        headers = ["#", "Name", "Age", "Gender", "Seat"]
        xs      = [50, 90, 300, 370, 460]
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica-Bold", 10)
        for h, x in zip(headers, xs):
            c.drawString(x, H-305, h)

        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        y = H-325
        for i, p in enumerate(pax_list):
            c.drawString(xs[0], y, str(i+1))
            c.drawString(xs[1], y, p["name"])
            c.drawString(xs[2], y, str(p["age"]))
            c.drawString(xs[3], y, p["gender"])
            c.setFillColor(colors.HexColor("#f9a826"))
            c.drawString(xs[4], y, p["seat"])
            c.setFillColor(colors.white)
            y -= 22

        c.setFillColor(colors.HexColor("#1e1b4b"))
        c.roundRect(30, H-530, W-60, 55, 12, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#4ade80"))
        c.setFont("Helvetica-Bold", 15)
        c.drawString(50, H-503, f"Total Amount Paid: Rs.{total:,.0f}")
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica", 10)
        c.drawRightString(W-50, H-503, "Payment: SUCCESS")

        rng2 = random.Random(booking_id)
        c.setFillColor(colors.HexColor("#f9a826"))
        for i in range(0, int(W-60), 8):
            ht = rng2.randint(20, 55)
            c.rect(30+i, H-610, 4, ht, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(W/2, 40, "Thank you for flying with SkyBook  |  Have a safe journey!")
        c.drawCentredString(W/2, 25, f"Ticket generated on {datetime.now().strftime('%d %b %Y %H:%M')}")
        c.save()
        buf.seek(0)
        return buf

    pdf_buf = make_ticket_pdf(booking_id, f, pax, tdate, total)

    st.download_button(
        label="📥  Download Boarding Pass (PDF)",
        data=pdf_buf,
        file_name=f"SkyBook_Ticket_{booking_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.markdown("### 🗒 Trip Summary")
    for p in pax:
        st.markdown(f"""
        <div class="card" style="padding:1rem 1.4rem;">
          <b style="color:#f9a826">{p['name']}</b> &nbsp;·&nbsp;
          <span style="color:#aaa">Age {p['age']} · {p['gender']}</span>
          &nbsp;&nbsp;<span class="badge">Seat {p['seat']}</span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🔄  Book Another Flight"):
        keys_to_clear = ["step","chosen_flight","travel_date","n_pax","pax_details",
                         "selected_seats","booking_id","total","flight_results",
                         "search_src","search_dst","search_date","search_npax"]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        st.session_state.step = "search"
        st.rerun()
