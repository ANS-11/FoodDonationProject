import streamlit as st
from auth_db import connect_db, verify_password, hash_password
from geopy.geocoders import Nominatim


# ------------------------------------------------
# CACHE GEOCODER (SAFE TO CACHE)
# ------------------------------------------------
@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="food_donation_app")

geolocator = get_geolocator()


# ------------------------------------------------
# REDIRECT IF ALREADY LOGGED IN
# ------------------------------------------------
if st.session_state.get("logged_in"):

    role = st.session_state.role

    if role == "Admin":
        st.switch_page("pages/admin.py")
    elif role == "Donor":
        st.switch_page("pages/donor.py")
    else:
        st.switch_page("pages/recipient.py")


# ------------------------------------------------
# UI
# ------------------------------------------------
st.title("🔐 Welcome")

option = st.radio(
    "Select Option",
    ["Login", "Register"],
    horizontal=True
)


# =====================================================
# LOGIN
# =====================================================
if option == "Login":

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and verify_password(password, user["password"]):

            st.session_state.logged_in = True
            st.session_state.user_id = user["id"]
            st.session_state.name = user["name"]
            st.session_state.role = user["role"]

            st.success("Login successful!")

            if user["role"] == "Admin":
                st.switch_page("pages/admin.py")
            elif user["role"] == "Donor":
                st.switch_page("pages/donor.py")
            else:
                st.switch_page("pages/recipient.py")

        else:
            st.error("Invalid email or password")


# =====================================================
# REGISTER
# =====================================================
else:

    with st.form("register_form"):

        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")

        role = st.selectbox(
            "Role",
            ["Donor", "Recipient" , "Admin"]
        )

        address = st.text_input(
            "Enter full address",
            placeholder="Door No, Street, City"
        )

        submit = st.form_submit_button("Create Account")

    # ------------------------------------------------
    if submit:

        if not name or not email or not password or not address or not phone:
            st.warning("Please fill all fields")
            st.stop()

        if not phone.isdigit() or len(phone) != 10:
            st.error("Enter valid 10-digit phone number.")
            st.stop()

        conn = connect_db()
        cursor = conn.cursor()

        # CHECK IF USER EXISTS
        cursor.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        )

        existing_user = cursor.fetchone()

        # ---------------- EXISTING USER ----------------
        if existing_user:

            st.warning("Account already exists.")
            new_address = st.text_input("Update address")

            if st.button("Update Address"):

                location = geolocator.geocode(new_address)

                if location:

                    cursor.execute("""
                        UPDATE users
                        SET city=?, lat=?, lon=?
                        WHERE email=?
                    """, (
                        new_address,
                        location.latitude,
                        location.longitude,
                        email
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Address updated successfully!")

                else:
                    st.error("Address not found.")

        # ---------------- NEW USER ----------------
        else:

            location = geolocator.geocode(address)

            if location is None:
                st.error("Address not found.")
                conn.close()
                st.stop()

            cursor.execute("""
                INSERT INTO users
                (name, email, password, role, city, lat, lon, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                email,
                hash_password(password),
                role,
                address,
                location.latitude,
                location.longitude,
                phone
            ))

            conn.commit()
            conn.close()

            st.success("Account created successfully! Please login.")