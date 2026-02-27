import streamlit as st
import pandas as pd
from auth_db import connect_db


# ------------------------------------------------
# PAGE PROTECTION
# ------------------------------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/auth.py")
    st.stop()

if st.session_state.role != "Admin":
    st.error("Admin access only.")
    st.stop()


# ------------------------------------------------
# LOGOUT
# ------------------------------------------------
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.switch_page("pages/auth.py")
    st.stop()


# ------------------------------------------------
# UI
# ------------------------------------------------
st.title("📊 Admin Dashboard")

st.write(f"Welcome Admin **{st.session_state.name}** 👋")

st.divider()


# ------------------------------------------------
# DATABASE
# ------------------------------------------------
conn = connect_db()

users = pd.read_sql("""
    SELECT id, name, email, role, city
    FROM users
""", conn)

donations = pd.read_sql("""
    SELECT Food_ID,
           Food_Name,
           Quantity,
           Location,
           Provider_Type,
           Provider_ID
    FROM food_listings
""", conn)

conn.close()


# ------------------------------------------------
# DISPLAY
# ------------------------------------------------
st.subheader("👥 Registered Users")
st.dataframe(users, use_container_width=True)

st.subheader("🍱 Available Donations")
st.dataframe(donations, use_container_width=True)


# ------------------------------------------------
# QUICK STATS (makes your project look advanced)
# ------------------------------------------------
st.divider()

col1, col2, col3 = st.columns(3)

col1.metric("Total Users", len(users))
col2.metric("Total Donations", len(donations))
col3.metric(
    "Active Donors",
    users[users["role"] == "Donor"].shape[0]
)
