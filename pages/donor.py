import streamlit as st
from auth_db import connect_db
from email_utils import send_email
from datetime import datetime, time
from recommend_food import load_model


# ------------------------------------------------
# LOAD ML MODEL
# ------------------------------------------------
@st.cache_resource
def get_model():
    return load_model()

model = get_model()


# ------------------------------------------------
# PAGE SECURITY
# ------------------------------------------------
if not st.session_state.get("logged_in"):
    st.switch_page("pages/auth.py")
    st.stop()

if st.session_state.role != "Donor":
    st.error("Access denied.")
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
st.title("🤝 Donor Dashboard")
st.write(f"Welcome **{st.session_state.name}**")
st.divider()


# =========================================================
# LOAD REQUESTS
# =========================================================
def load_requests(donor_id):

    conn = connect_db()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT 
        r.request_id,
        u.name,
        u.email,
        u.phone,
        f.Food_ID,
        f.Food_Name,
        f.Quantity,
        r.quantity_requested
        FROM requests r
        JOIN users u ON r.recipient_id = u.id
        JOIN food_listings f ON r.food_id = f.Food_ID
        WHERE r.donor_id=? AND r.status='PENDING'
    """, (donor_id,)).fetchall()

    conn.close()
    return rows


# =========================================================
# REQUESTS UI
# =========================================================
st.header("📥 Incoming Requests")

requests = load_requests(st.session_state.user_id)

if not requests:
    st.info("No pending requests.")

else:
    for req in requests:

        (
            req_id,
            recipient_name,
            recipient_email,
            phone,
            food_id,
            food,
            available_qty,
            requested_qty
        ) = req

        st.write("------")
        st.write(f"👤 Recipient: {recipient_name}")
        st.write(f"📞 Phone: {phone}")
        st.write(f"🍲 Food: {food}")
        st.write(f"📦 Requested: {requested_qty}")
        st.write(f"📦 Available: {available_qty}")

        col1, col2 = st.columns(2)

        # ===================== APPROVE =====================
        if col1.button("Approve", key=f"a_{req_id}"):

            conn = connect_db()
            cursor = conn.cursor()

            if available_qty < requested_qty:
                st.error("Not enough quantity available!")
                conn.close()
            else:
                cursor.execute("""
                    UPDATE food_listings
                    SET Quantity = Quantity - ?
                    WHERE Food_ID = ?
                """, (requested_qty, food_id))

                cursor.execute("""
                    UPDATE requests
                    SET status='APPROVED'
                    WHERE request_id=?
                """, (req_id,))

                conn.commit()
                conn.close()

                # ✅ SEND APPROVAL EMAIL
                send_email(
                    recipient_email,
                    "✅ Food Request Approved",
                    f"""
Hello {recipient_name},

🎉 Your food request has been APPROVED!

Food Item: {food}
Approved Quantity: {requested_qty}

Please login to the Food Donation Portal to view pickup details.

Thank you for reducing food waste 💚
"""
                )

                st.success("Request Approved!")
                st.rerun()

        # ===================== REJECT =====================
        if col2.button("Reject", key=f"r_{req_id}"):

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE requests
                SET status='REJECTED'
                WHERE request_id=?
            """, (req_id,))

            conn.commit()
            conn.close()

            # ❌ SEND REJECTION EMAIL
            send_email(
                recipient_email,
                "❌ Food Request Rejected",
                f"""
Hello {recipient_name},

We are sorry 😔.

Your request for "{food}" was rejected by the donor.

Please login and request from another nearby donor.

Thank you for understanding.
"""
            )

            st.warning("Request Rejected.")
            st.rerun()


# =========================================================
# DONATION FORM
# =========================================================
st.divider()
st.subheader("Donate Food")

with st.form("donation_form"):

    food_name = st.text_input("Food Name")

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        step=1
    )

    food_type = st.selectbox(
        "Food Type",
        ["Freshly Cooked", "Packaged", "Bakery", "Fruits/Vegetables"]
    )

    expiry_date = st.date_input("Expiry Date")

    if food_type == "Freshly Cooked":
        expiry_time = st.time_input("Expiry Time")
        expiry_datetime = datetime.combine(expiry_date, expiry_time)
    else:
        expiry_datetime = datetime.combine(expiry_date, time(23, 59))

    provider_type = st.selectbox(
        "Provider Type",
        ["Restaurant", "Individual", "Catering", "Grocery Store"]
    )

    submitted = st.form_submit_button("Submit Donation")


# =========================================================
# SUBMIT DONATION
# =========================================================
if submitted:

    if not food_name:
        st.warning("Please enter food name.")
        st.stop()

    current_time = datetime.now()

    if expiry_datetime < current_time:
        st.error("Food already expired.")
        st.stop()

    time_difference = expiry_datetime - current_time
    days_to_expiry = time_difference.total_seconds() / (60 * 60 * 24)

    prediction = model.predict([[quantity, days_to_expiry]])

    safety_status = "SAFE" if prediction[0] == 1 else "UNSAFE"

    conn = connect_db()
    cursor = conn.cursor()

    user_data = cursor.execute(
        "SELECT city, lat, lon FROM users WHERE id=?",
        (st.session_state.user_id,)
    ).fetchone()

    cursor.execute("""
        INSERT INTO food_listings
        (Food_Name, Quantity, Location, Provider_Type,
         Provider_ID, lat, lon, Expiry_Date,
         days_to_expiry, Safety_Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        food_name,
        quantity,
        user_data["city"],
        provider_type,
        st.session_state.user_id,
        user_data["lat"],
        user_data["lon"],
        expiry_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        days_to_expiry,
        safety_status
    ))

    conn.commit()
    conn.close()

    if safety_status == "SAFE":
        st.success("Donation submitted successfully!")
    else:
        st.warning("Food marked UNSAFE.")

    st.rerun()