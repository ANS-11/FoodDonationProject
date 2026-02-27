import streamlit as st

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Food Donation System",
    layout="wide"
)

# -------------------------------------------------
# SESSION INITIALIZATION
# -------------------------------------------------
DEFAULT_SESSION = {
    "logged_in": False,
    "role": None,
    "name": None,
    "user_id": None,
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------------------------------------
# NOT LOGGED IN → LANDING PAGE
# -------------------------------------------------
if not st.session_state.logged_in:

    st.title("🍲 Zero Waste Food Donation System")

    st.markdown("""
Welcome to the smart food donation platform.

✅ Donors donate excess food  
✅ Recipients request food  
✅ Intelligent matching reduces waste
""")

    st.image(
        "https://images.unsplash.com/photo-1593113630400-ea4288922497",
        use_container_width=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Login", use_container_width=True):
            st.switch_page("pages/auth.py")

    with col2:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("pages/auth.py")   # ✅ FIXED

    st.stop()


# -------------------------------------------------
# LOGGED IN → AUTO REDIRECT
# -------------------------------------------------
role = st.session_state.role

if role == "Admin":
    st.switch_page("pages/admin.py")

elif role == "Donor":
    st.switch_page("pages/donor.py")

elif role == "Recipient":
    st.switch_page("pages/recipient.py")

else:
    st.session_state.clear()
    st.warning("Session error. Please login again.")
    st.switch_page("app.py")