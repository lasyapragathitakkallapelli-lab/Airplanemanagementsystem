import streamlit as st
import mysql.connector
import pandas as pd
import random
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

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

/* ── SEAT MAP ── */
.seat-grid { display: flex; flex-direction: column; gap: 6px; align-items: center; margin: 1rem 0; }
.seat-row  { display: flex; gap: 6px; align-items: center; }
.seat-label { width: 24px; color: #aaa; font-size: 0.75rem; text-align: center; font-family: 'Space Mono'; }
.seat {
    width: 36px; height: 36px;
    border-radius: 8px 8px 4px 4px;
    border: none;
    cursor: pointer;
    font-size: 0.65rem;
    font-weight: 700;
    font-family: 'Space Mono';
    transition: transform 0.1s;
}
.seat:hover { transform: scale(1.1); }
.seat-free     { background: #334155; color: #94a3b8; }
.seat-selected { background: #f9a826; color: #0f0c29; }
.seat-booked   { background: #374151; color: #4b5563; cursor: not-allowed; opacity: 0.5; }
.seat-aisle    { width: 16px; }
.seat-cols-header { display: flex; gap: 6px; margin-bottom: 4px; align-items: center; }
.seat-col-label { width: 36px; text-align: center; color: #64748b; font-size: 0.7rem; font-family:'Space Mono'; }

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
section[data-testid="stSidebar"] .stSelectbox > div > div { background: rgba(255,255,255,0.05) !important; }

/* ── SUCCESS / ERROR ── */
.stSuccess { background: rgba(74,222,128,0.1) !important; border-color: #4ade80 !important; }
.stError   { background: rgba(239,68,68,0.1) !important; border-color: #ef4444 !important; }

/* divider */
hr { border-color: rgba(255,255,255,0.08) !important; }

/* hide hamburger */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# DB CONNECTION  (cached)
# ─────────────────────────────────────────
@st.cache_resource
def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="kalabairava_@13",   # ← change if needed
        database="airline_portals",
        autocommit=False
    )

conn = get_conn()

def run(sql, params=(), fetch=True):
    """Execute SQL safely, return rows if fetch=True."""
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        st.error(f"DB error: {e}")
        return [] if fetch else None

# ─────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────
defaults = {
    "user": None,
    "step": "search",           # search | seats | payment | done
    "chosen_flight": None,
    "travel_date": None,
    "n_pax": 1,
    "pax_details": [],          # list of dicts {name,age,gender}
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
                run("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                    (un, em, pw), fetch=False)
                st.success("Account created! Please login.")

    elif menu == "Login":
        if st.session_state.user is None:
            with st.form("login_form"):
                un = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    rows = run("SELECT * FROM users WHERE username=%s AND password=%s", (un, pw))
                    if rows:
                        st.session_state.user = rows[0]
                        st.session_state.step = "search"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        else:
            st.success(f"👋 {st.session_state.user[1]}")
            if st.button("Logout"):
                for k in defaults:
                    st.session_state[k] = defaults[k]
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
      <p style="color:#aaa;">Use the sidebar → Login to get started</p>
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
            rows = run("SELECT * FROM flights WHERE source=%s AND destination=%s", (src, dst))
            if not rows:
                st.warning("No flights found for this route.")
            else:
                st.session_state["flight_results"] = rows
                st.session_state["search_src"]    = src
                st.session_state["search_dst"]    = dst
                st.session_state["search_date"]   = tdate
                st.session_state["search_npax"]   = n_pax

    # Show results (persists across reruns)
    if "flight_results" in st.session_state and st.session_state.flight_results:
        st.markdown("---")
        st.markdown(f"### Available Flights · {st.session_state.search_src} → {st.session_state.search_dst}")

        flights_to_show = []
        seen = set()
        for f in st.session_state.flight_results:
            # Show up to 8 distinct flights per route
            if len(flights_to_show) >= 8:
                break
            key_sig = f"{f[0]}"
            if key_sig not in seen:
                seen.add(key_sig)
                flights_to_show.append(f)

        for f in flights_to_show:
            dep = str(f[4])[:5]
            arr = str(f[5])[:5]
            # Compute rough duration
            try:
                d1 = datetime.strptime(dep, "%H:%M")
                d2 = datetime.strptime(arr, "%H:%M")
                diff = (d2 - d1).seconds // 60
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
                  <div class="card-price" style="margin-top:0.5rem;">₹{f[6]:,} <span style="font-size:0.85rem;color:#aaa;">/ person</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button(f"Book →", key=f"book_{f[0]}"):
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
    f    = st.session_state.chosen_flight
    n    = st.session_state.n_pax
    dep  = str(f[4])[:5]
    arr  = str(f[5])[:5]

    st.markdown(f"""
    <div class="card">
      <div class="card-title">✈ {f[1]}</div>
      <div class="card-route">{f[2]} → {f[3]}</div>
      <div class="card-meta">🗓 {st.session_state.travel_date} &nbsp;·&nbsp; 🕐 {dep} → {arr} &nbsp;·&nbsp; {n} passenger(s)</div>
      <div class="card-price">Total: ₹{f[6]*n:,}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SEAT MAP ────────────────────────────
    st.markdown("### 💺 Choose Your Seats")
    st.caption(f"Select exactly {n} seat(s). Click to toggle.")

    # Pre-occupied seats (random, consistent per flight)
    rng = random.Random(f[0])
    COLS = ["A","B","C","D","E","F"]
    ROWS = 20
    occupied = set(
        f"{rng.randint(1,ROWS)}{rng.choice(COLS)}"
        for _ in range(30)
    )

    if "selected_seats" not in st.session_state:
        st.session_state.selected_seats = []

    # Build HTML seat grid
    col_header = '<div class="seat-cols-header"><div class="seat-label"> </div>'
    for col in COLS:
        if col == "D":
            col_header += '<div class="seat-aisle"></div>'
        col_header += f'<div class="seat-col-label">{col}</div>'
    col_header += "</div>"

    seat_html = f'<div class="seat-grid">{col_header}'
    for row in range(1, ROWS+1):
        seat_html += f'<div class="seat-row"><div class="seat-label">{row}</div>'
        for col in COLS:
            if col == "D":
                seat_html += '<div class="seat-aisle"></div>'
            seat = f"{row}{col}"
            if seat in occupied:
                cls = "seat-booked"
            elif seat in st.session_state.selected_seats:
                cls = "seat-selected"
            else:
                cls = "seat-free"
            seat_html += f'<div class="seat {cls}" title="{seat}">{seat}</div>'
        seat_html += "</div>"
    seat_html += "</div>"

    st.markdown(seat_html, unsafe_allow_html=True)

    # Legend
    st.markdown("""
    <div style="display:flex;gap:16px;margin:0.5rem 0 1rem;font-size:0.8rem;color:#aaa;">
      <span><span style="background:#334155;padding:2px 8px;border-radius:4px;">&nbsp;</span> Available</span>
      <span><span style="background:#f9a826;padding:2px 8px;border-radius:4px;">&nbsp;</span> Selected</span>
      <span><span style="background:#374151;padding:2px 8px;border-radius:4px;opacity:0.5;">&nbsp;</span> Taken</span>
    </div>
    """, unsafe_allow_html=True)

    # Seat input via text (since we can't do JS click → Python easily)
    st.markdown("**Type seat numbers to select** (e.g. `3A`, `5C`)")
    seat_input = st.text_input(
        f"Enter {n} seat(s), comma-separated",
        value=", ".join(st.session_state.selected_seats),
        placeholder="e.g. 3A, 7C, 12F",
        label_visibility="collapsed"
    )
    if st.button("✔ Confirm Seats"):
        raw = [s.strip().upper() for s in seat_input.split(",") if s.strip()]
        valid = [s for s in raw if
                 len(s) >= 2 and
                 s[:-1].isdigit() and
                 1 <= int(s[:-1]) <= ROWS and
                 s[-1] in COLS and
                 s not in occupied]
        unique = list(dict.fromkeys(valid))  # deduplicate preserving order
        if len(unique) != n:
            st.error(f"Please select exactly {n} valid, available seat(s). Got {len(unique)}.")
        else:
            st.session_state.selected_seats = unique
            st.success(f"Seats confirmed: {', '.join(unique)}")

    # ── PASSENGER DETAILS ────────────────────
    if len(st.session_state.selected_seats) == n:
        st.markdown("### 👤 Passenger Details")
        pax_list = []
        all_filled = True
        for i in range(n):
            with st.expander(f"Passenger {i+1} – Seat {st.session_state.selected_seats[i]}", expanded=True):
                c1, c2, c3 = st.columns(3)
                nm  = c1.text_input("Full Name",   key=f"pname_{i}")
                age = c2.number_input("Age", 1, 100, key=f"page_{i}")
                gen = c3.selectbox("Gender", ["Male","Female","Other"], key=f"pgen_{i}")
                if not nm.strip():
                    all_filled = False
                pax_list.append({"name": nm, "age": age, "gender": gen,
                                 "seat": st.session_state.selected_seats[i]})

        if all_filled:
            st.session_state.pax_details = pax_list
            st.markdown("<br>", unsafe_allow_html=True)
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
# STEP 3 – PAYMENT  (fake / demo mode)
# ═══════════════════════════════════════════
elif st.session_state.step == "payment":
    import time

    f      = st.session_state.chosen_flight
    n      = st.session_state.n_pax
    total  = f[6] * n
    pax    = st.session_state.pax_details
    tdate  = st.session_state.travel_date

    # ── Booking Summary card ─────────────────
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
      <table style="width:100%;margin-top:1rem;border-collapse:collapse;">
        {pax_html}
      </table>
      <hr style="margin:1rem 0;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="color:#aaa;">Base fare × {n} &nbsp;+&nbsp; taxes</span>
        <div class="card-price">₹{total:,}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Payment Method selector ──────────────
    st.markdown("### 💳 Payment Method")
    method = st.radio("", ["UPI", "Credit / Debit Card", "Net Banking", "Wallet"],
                      horizontal=True, label_visibility="collapsed")

    # ── Fake input fields per method ─────────
    if method == "UPI":
        st.markdown("""
        <div class="card" style="padding:1.2rem 1.4rem;">
          <div style="color:#f9a826;font-weight:700;margin-bottom:0.8rem;">📱 UPI Payment</div>
        """, unsafe_allow_html=True)
        upi_id = st.text_input("UPI ID", placeholder="yourname@upi", key="upi_id")
        st.markdown('</div>', unsafe_allow_html=True)
        # Fake QR hint
        st.markdown("""
        <div style="text-align:center;padding:0.8rem;background:rgba(255,255,255,0.04);
                    border-radius:12px;border:1px dashed rgba(255,255,255,0.15);margin-top:0.5rem;">
          <div style="font-size:2rem;">📲</div>
          <div style="color:#aaa;font-size:0.8rem;">Or scan QR code at the counter</div>
          <div style="color:#f9a826;font-size:0.75rem;margin-top:4px;">Demo mode — no real transaction</div>
        </div>
        """, unsafe_allow_html=True)

    elif method == "Credit / Debit Card":
        st.markdown("""
        <div class="card" style="padding:1.2rem 1.4rem;">
          <div style="color:#f9a826;font-weight:700;margin-bottom:0.8rem;">💳 Card Details</div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.text_input("Card Number", value="4111 1111 1111 1111", key="card_num")
        c2.text_input("Name on Card", placeholder="As on card", key="card_name")
        c3, c4 = st.columns(2)
        c3.text_input("Expiry", value="12/26", key="card_exp")
        c4.text_input("CVV", value="123", type="password", key="card_cvv")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="color:#64748b;font-size:0.75rem;margin-top:4px;">
          🔒 Demo card pre-filled — no real charge will be made
        </div>""", unsafe_allow_html=True)

    elif method == "Net Banking":
        st.markdown("""
        <div class="card" style="padding:1.2rem 1.4rem;">
          <div style="color:#f9a826;font-weight:700;margin-bottom:0.8rem;">🏦 Net Banking</div>
        """, unsafe_allow_html=True)
        bank = st.selectbox("Select Your Bank", ["SBI","HDFC","ICICI","Axis","Kotak","PNB","BOB"], key="nb_bank")
        st.markdown(f"""
          <div style="margin-top:0.6rem;padding:0.6rem 1rem;background:rgba(249,168,38,0.08);
                      border-radius:8px;border:1px solid rgba(249,168,38,0.2);">
            <span style="color:#aaa;font-size:0.85rem;">You will be redirected to</span>
            <b style="color:#f9a826;"> {bank} NetBanking portal</b>
            <span style="color:#64748b;font-size:0.75rem;display:block;margin-top:4px;">
              (Demo only — no redirect will happen)
            </span>
          </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:  # Wallet
        st.markdown("""
        <div class="card" style="padding:1.2rem 1.4rem;">
          <div style="color:#f9a826;font-weight:700;margin-bottom:0.8rem;">👛 Wallet</div>
        """, unsafe_allow_html=True)
        wallet_ph = st.text_input("Wallet / Phone Number", value="9876543210", key="wallet_ph")
        st.markdown("""
          <div style="color:#4ade80;font-size:0.8rem;margin-top:6px;">
            ✅ Wallet Balance: ₹50,000 (Demo)
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Action buttons ───────────────────────
    col_back, col_pay = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            st.session_state.step = "seats"
            st.rerun()
    with col_pay:
        pay_btn = st.button(f"💰  Pay ₹{total:,} Now", use_container_width=True)

    # ── Fake payment processing ──────────────
    if pay_btn:
        # Step 1 – "Contacting bank"
        status_box = st.empty()
        status_box.markdown("""
        <div class="card" style="text-align:center;padding:1.5rem;">
          <div style="font-size:2rem;">🔄</div>
          <div style="color:#f9a826;font-weight:700;margin-top:0.5rem;">Contacting payment gateway…</div>
          <div style="color:#aaa;font-size:0.8rem;">Please do not close this window</div>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)

        # Step 2 – "Verifying"
        status_box.markdown("""
        <div class="card" style="text-align:center;padding:1.5rem;">
          <div style="font-size:2rem;">🔐</div>
          <div style="color:#f9a826;font-weight:700;margin-top:0.5rem;">Verifying your details…</div>
          <div style="color:#aaa;font-size:0.8rem;">Authenticating with your bank</div>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)

        # Step 3 – "Processing"
        status_box.markdown("""
        <div class="card" style="text-align:center;padding:1.5rem;">
          <div style="font-size:2rem;">💸</div>
          <div style="color:#f9a826;font-weight:700;margin-top:0.5rem;">Processing payment…</div>
          <div style="color:#aaa;font-size:0.8rem;">Almost there!</div>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)

        # Step 4 – fake txn ID & save to DB
        fake_txn = f"TXN{''.join([str(random.randint(0,9)) for _ in range(12)])}"

        status_box.markdown(f"""
        <div class="card" style="text-align:center;padding:1.5rem;
             border-color:rgba(74,222,128,0.4);">
          <div style="font-size:2.5rem;">✅</div>
          <div style="color:#4ade80;font-weight:800;font-size:1.2rem;margin-top:0.5rem;">
            Payment Successful!
          </div>
          <div style="color:#aaa;font-size:0.8rem;margin-top:0.4rem;">
            Transaction ID: <b style="color:#f9a826;">{fake_txn}</b>
          </div>
        </div>""", unsafe_allow_html=True)
        time.sleep(0.8)

        # Save to DB
        booking_id = run(
            "INSERT INTO bookings(user_id,flight_id,travel_date,total_amount) VALUES(%s,%s,%s,%s)",
            (st.session_state.user[0], f[0], tdate, total), fetch=False
        )
        if booking_id:
            for p in pax:
                run(
                    "INSERT INTO passengers(booking_id,name,age,gender,seat_no) VALUES(%s,%s,%s,%s,%s)",
                    (booking_id, p["name"], p["age"], p["gender"], p["seat"]), fetch=False
                )
            run(
                "INSERT INTO payments(booking_id,payment_method,amount,payment_status) VALUES(%s,%s,%s,%s)",
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

    # ── Generate PDF Ticket ────────────────
    def make_ticket_pdf(booking_id, flight, pax_list, travel_date, total):
        buf = BytesIO()
        c   = canvas.Canvas(buf, pagesize=A4)
        W, H = A4

        # Background
        c.setFillColor(colors.HexColor("#0f0c29"))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # Header band
        c.setFillColor(colors.HexColor("#f9a826"))
        c.rect(0, H-100, W, 100, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#0f0c29"))
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(W/2, H-55, "✈  SkyBook  |  BOARDING PASS")
        c.setFont("Helvetica", 11)
        c.drawCentredString(W/2, H-78, "Airline Reservation System")

        # Flight info box
        c.setFillColor(colors.HexColor("#1e1b4b"))
        c.roundRect(30, H-260, W-60, 145, 12, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#f9a826"))
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, H-140, flight[1])            # flight name

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(50, H-185, flight[2])
        c.drawString(W-160, H-185, flight[3])
        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawCentredString(W/2, H-185, "───────── ✈ ─────────")
        c.drawCentredString(W/2, H-205, f"Dep: {str(flight[4])[:5]}  |  Arr: {str(flight[5])[:5]}")

        # Date / Booking
        c.setFillColor(colors.HexColor("#f9a826"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, H-235, f"Date: {travel_date}")
        c.drawRightString(W-50, H-235, f"Booking ID: #{booking_id}")

        # Passenger table
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

        # Total
        c.setFillColor(colors.HexColor("#1e1b4b"))
        c.roundRect(30, H-530, W-60, 55, 12, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#4ade80"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, H-503, f"Total Amount Paid: ₹{total:,}")
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica", 10)
        c.drawRightString(W-50, H-503, "Payment: SUCCESS ✓")

        # Barcode-style decoration
        c.setFillColor(colors.HexColor("#f9a826"))
        for i in range(0, int(W-60), 8):
            ht = random.randint(20, 55)
            c.rect(30+i, H-610, 4, ht, fill=1, stroke=0)

        # Footer
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(W/2, 40, "Thank you for flying with SkyBook • Have a safe journey!")
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

    # Details
    st.markdown("### 🗒 Trip Summary")
    for i, p in enumerate(pax):
        st.markdown(f"""
        <div class="card" style="padding:1rem 1.4rem;">
          <b style="color:#f9a826">{p['name']}</b> &nbsp;·&nbsp;
          <span style="color:#aaa">Age {p['age']} · {p['gender']}</span>
          &nbsp;&nbsp;<span class="badge">Seat {p['seat']}</span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🔄  Book Another Flight"):
        for k in ["step","chosen_flight","travel_date","n_pax","pax_details",
                  "selected_seats","booking_id","total","flight_results"]:
            if k in st.session_state:
                del st.session_state[k]
        st.session_state.step = "search"
        st.rerun()