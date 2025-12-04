import streamlit as st
import random
import string
import os
import json

st.set_page_config(page_title="Bennett Movies — Book Tickets", layout="wide")

# -----------------------------
# Admin Credentials
# -----------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

DB_FILE = "movies_data.json"

# -----------------------------
# Data Handling
# -----------------------------
def load_data_from_db():
    if not os.path.exists(DB_FILE):
        return {"movies": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data_to_db():
    movies_to_save = st.session_state.movies
    for movie in movies_to_save:
        mid = movie["id"]
        movie["booked_seats"] = sorted(list(st.session_state.booked.get(mid, [])))
    with open(DB_FILE, "w") as f:
        json.dump({"movies": movies_to_save}, f, indent=2)

# -----------------------------
# App State Init
# -----------------------------
def init_app_state():
    if "movies" not in st.session_state:
        data = load_data_from_db()
        st.session_state.movies = data.get("movies", [])
        st.session_state.booked = {
            m["id"]: set(m.get("booked_seats", [])) for m in st.session_state.movies
        }

    if "view_movie" not in st.session_state:
        st.session_state.view_movie = None

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

init_app_state()

# -----------------------------
# Utility Functions
# -----------------------------
def generate_seat_ids(movie):
    seats = []
    for r in range(movie["rows"]):
        row = []
        for c in range(movie["cols"]):
            row.append(chr(ord("A")+r) + str(c+1))
        seats.append(row)
    return seats

def generate_ticket_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# -----------------------------
# UI Start
# -----------------------------
st.title("🎬 Bennett Movies — Ticket Booking")

tab1, tab2 = st.tabs(["🎟 User Booking", "🛠 Admin Dashboard"])

# ==================================================
# ================= USER BOOKING ===================
# ==================================================
with tab1:
    movies = st.session_state.movies

    if not movies:
        st.warning("No movies found in database.")
    else:
        st.subheader("Now Showing")

        cols = st.columns(3)
        for idx, movie in enumerate(movies):
            with cols[idx % 3]:
                st.image(movie["poster"], width=200)
                st.subheader(movie["title"])
                st.write(movie["genre"])
                st.write("⭐", movie["rating"])
                if st.button("View & Book", key=f"view_{movie['id']}"):
                    st.session_state.view_movie = movie["id"]
                    st.rerun()

    # -----------------------------
    # Seat Booking
    # -----------------------------
    if st.session_state.view_movie:
        movie = next(m for m in movies if m["id"] == st.session_state.view_movie)
        st.header(movie["title"])

        seats = generate_seat_ids(movie)
        booked = st.session_state.booked[movie["id"]]

        selected_seats = []

        for row in seats:
            cols = st.columns(len(row))
            for i, seat in enumerate(row):
                disabled = seat in booked
                if cols[i].checkbox(seat, disabled=disabled, key=f"{movie['id']}_{seat}"):
                    selected_seats.append(seat)

        st.markdown("---")
        name = st.text_input("Full Name")
        phone = st.text_input("Phone")

        total_price = len(selected_seats) * 150
        st.metric("Total Amount", f"₹{total_price}")

        if st.button("Book Tickets"):
            if not name or not phone:
                st.error("Enter Name & Phone")
            elif not selected_seats:
                st.error("Select at least one seat")
            else:
                for s in selected_seats:
                    st.session_state.booked[movie["id"]].add(s)
                save_data_to_db()

                ticket = generate_ticket_id()
                st.success(f"✅ Ticket Booked | ID: {ticket}")
                st.balloons()
                st.session_state.view_movie = None
                st.rerun()

        if st.button("Back"):
            st.session_state.view_movie = None
            st.rerun()

# ==================================================
# ================= ADMIN PANEL ====================
# ==================================================
with tab2:
    st.header("🛠 Admin Dashboard")

    if not st.session_state.admin_auth:
        user = st.text_input("Admin Username")
        pwd = st.text_input("Admin Password", type="password")

        if st.button("Login"):
            if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.success("Admin Login Successful")
                st.rerun()
            else:
                st.error("Invalid Credentials")
        st.stop()

    st.success("Welcome Admin ✅")

    # -----------------------------
    # Movie Management
    # -----------------------------
    for movie in st.session_state.movies:
        total = movie["rows"] * movie["cols"]
        booked = len(st.session_state.booked[movie["id"]])
        available = total - booked

        with st.expander(movie["title"]):
            st.write("Total:", total)
            st.write("Booked:", booked)
            st.write("Available:", available)

            c1, c2 = st.columns(2)

            with c1:
                if st.button("🧹 Clear Bookings", key=f"clear_{movie['id']}"):
                    st.session_state.booked[movie["id"]] = set()
                    movie["booked_seats"] = []
                    save_data_to_db()
                    st.rerun()

            with c2:
                if st.button("❌ Delete Movie", key=f"del_{movie['id']}"):
                    st.session_state.movies = [m for m in st.session_state.movies if m["id"] != movie["id"]]
                    del st.session_state.booked[movie["id"]]
                    save_data_to_db()
                    st.rerun()

    # -----------------------------
    # Add New Movie
    # -----------------------------
    st.markdown("---")
    st.subheader("➕ Add New Movie")

    nid = st.text_input("Movie ID")
    title = st.text_input("Title")
    genre = st.text_input("Genre")
    duration = st.text_input("Duration")
    rating = st.text_input("Rating")
    poster = st.text_input("Poster URL")
    rows = st.number_input("Rows", 5, 20, 10)
    cols = st.number_input("Columns", 5, 20, 12)

    if st.button("✅ Add Movie"):
        new_movie = {
            "id": nid,
            "title": title,
            "genre": genre,
            "duration": duration,
            "rating": rating,
            "poster": poster,
            "rows": rows,
            "cols": cols,
            "booked_seats": []
        }

        st.session_state.movies.append(new_movie)
        st.session_state.booked[nid] = set()
        save_data_to_db()
        st.success("Movie Added")
        st.rerun()

    # -----------------------------
    # Logout
    # -----------------------------
    if st.button("🚪 Logout Admin"):
        st.session_state.admin_auth = False
        st.rerun()
