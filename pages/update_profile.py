import streamlit as st
from auth_db import connect_db, hash_password
from geocode_setup import geocode_address


# ------------------------------------------------
# LOGIN PROTECTION
# ------------------------------------------------
if not st.session_state.get("logged_in"):
    st.switch_page("pages/auth.py")
    st.stop()

st.title("⚙️ Update Profile")

user_id = st.session_state.get("user_id")

conn = connect_db()
cursor = conn.cursor()

# ------------------------------------------------
# LOAD CURRENT USER DATA (SAFE VERSION)
# ------------------------------------------------
cursor.execute("""
SELECT name, email, phone, address
FROM users
WHERE id=?
""", (user_id,))

result = cursor.fetchone()

# ⭐ prevents NoneType crash
if result is None:
    st.error("User not found. Please login again.")
    st.session_state.clear()
    st.switch_page("pages/auth.py")
    st.stop()

name, email, phone, address = result


# ------------------------------------------------
# INPUT FIELDS
# ------------------------------------------------
st.subheader("Profile Information")

new_name = st.text_input("Name", value=name)
new_phone = st.text_input("Phone Number", value=phone)
new_address = st.text_input("Address", value=address)

st.divider()
st.subheader("🔐 Change Password (Optional)")

new_password = st.text_input(
    "New Password",
    type="password"
)

# ------------------------------------------------
# UPDATE BUTTON
# ------------------------------------------------
if st.button("✅ Update Profile"):

    # PHONE VALIDATION
    if not new_phone.isdigit() or len(new_phone) != 10:
        st.error("Enter valid 10-digit phone number.")
        st.stop()

    # GEOCODE ADDRESS
    with st.spinner("Updating location..."):
        lat, lon = geocode_address(new_address)

    if lat is None or lon is None:
        st.error("Address not found. Try full address.")
        st.stop()

    # ------------------------------------------------
    # UPDATE DATABASE
    # ------------------------------------------------
    if new_password:

        hashed_pw = hash_password(new_password)

        cursor.execute("""
        UPDATE users
        SET name=?,
            phone=?,
            address=?,
            lat=?,
            lon=?,
            password=?
        WHERE id=?
        """, (
            new_name,
            new_phone,
            new_address,
            lat,
            lon,
            hashed_pw,
            user_id
        ))

    else:
        cursor.execute("""
        UPDATE users
        SET name=?,
            phone=?,
            address=?,
            lat=?,
            lon=?
        WHERE id=?
        """, (
            new_name,
            new_phone,
            new_address,
            lat,
            lon,
            user_id
        ))

    conn.commit()
    conn.close()

    st.success("✅ Profile Updated Successfully!")
    st.rerun()