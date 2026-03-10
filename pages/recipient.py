import streamlit as st
from email_utils import send_email
from recommend_food import recommend_food
from auth_db import connect_db


# ------------------------------------------------
# SESSION STATE
# ------------------------------------------------
st.session_state.setdefault("search_results", None)
st.session_state.setdefault("success_msg", None)


# ------------------------------------------------
# PAGE SECURITY
# ------------------------------------------------
if not st.session_state.get("logged_in"):
    st.switch_page("pages/auth.py")
    st.stop()

if st.session_state.role != "Recipient":
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
st.title("🍽 Food Request Portal")
st.write(f"Welcome **{st.session_state.name}** 👋")
st.divider()

receiver_id = st.session_state.user_id


# ------------------------------------------------
# SUCCESS MESSAGE
# ------------------------------------------------
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None


# ------------------------------------------------
# SAFE FOOD LIST
# ------------------------------------------------
@st.cache_data(ttl=20)
def get_safe_foods():

    conn = connect_db()
    cursor = conn.cursor()

    foods = cursor.execute("""
        SELECT DISTINCT Food_Name
        FROM food_listings
        WHERE Safety_Status='SAFE'
        AND Quantity > 0
    """).fetchall()

    conn.close()

    return [f[0] for f in foods]


foods = get_safe_foods()

if not foods:
    st.warning("No safe food available right now.")
    st.stop()

food_type = st.selectbox("Food Type Needed", foods)


# ------------------------------------------------
# FIND DONOR
# ------------------------------------------------
if st.button("Find Nearest Safe Donor"):

    with st.spinner("🔎 Searching nearby safe donors..."):

        receiver, results = recommend_food(
            receiver_id,
            food_type,
            1
        )

    st.session_state.search_results = (receiver, results)


# ------------------------------------------------
# SHOW RESULTS
# ------------------------------------------------
if st.session_state.search_results:

    receiver, results = st.session_state.search_results

    name, city, lat, lon = receiver

    col1, col2 = st.columns(2)
    col1.write(f"👤 **Receiver:** {name}")
    col2.write(f"📍 **Location:** {city}")

    st.divider()

    if results.empty:
        st.error("❌ No safe donors available within your radius.")

    else:
        st.success("✅ Nearest Safe Donors Found!")

        for _, row in results.sort_values("distance_km").iterrows():

            st.write("------")
            st.write(f"🍲 **Food:** {row['Food_Name']}")
            st.write(f"📦 Quantity Available: {row['Quantity']}")
            st.write(f"🏪 Provider: {row['Provider_Type']}")
            st.write(f"📍 Distance: {round(row['distance_km'],2)} km")

            request_qty = st.number_input(
                "Request quantity",
                min_value=1,
                max_value=int(row['Quantity']),
                key=f"qty_{row['Food_ID']}"
            )

            if st.button("Send Request", key=f"req_{row['Food_ID']}"):

                conn = connect_db()
                cursor = conn.cursor()

                exists = cursor.execute("""
                    SELECT 1 FROM requests
                    WHERE food_id=? 
                    AND recipient_id=?
                    AND status='PENDING'
                """, (row['Food_ID'], receiver_id)).fetchone()

                if exists:
                    conn.close()
                    st.warning("Request already sent.")
                    st.stop()

                latest_qty, donor_id = cursor.execute("""
                    SELECT Quantity, Provider_ID
                    FROM food_listings
                    WHERE Food_ID=?
                """, (row['Food_ID'],)).fetchone()

                if request_qty > latest_qty:
                    conn.close()
                    st.error("Quantity exceeds available stock.")
                    st.stop()

                cursor.execute("""
                    INSERT INTO requests
                    (food_id, donor_id, recipient_id,
                     quantity_requested, status)
                    VALUES (?, ?, ?, ?, 'PENDING')
                """, (
                    row['Food_ID'],
                    donor_id,
                    receiver_id,
                    request_qty
                ))

                donor_email = cursor.execute(
                    "SELECT email FROM users WHERE id=?",
                    (donor_id,)
                ).fetchone()[0]

                conn.commit()
                conn.close()

                send_email(
                    donor_email,
                    "📩 New Food Request Received",
                    f"""
Hello,

You have received a new food request.

Food Item: {row['Food_Name']}
Requested Quantity: {request_qty}

Login to approve or reject.
"""
                )

                st.cache_data.clear()

                st.session_state.success_msg = (
                    "✅ Request sent successfully!"
                )

                st.rerun()


# =================================================
# ⭐ NEW SECTION — REQUEST STATUS DISPLAY ⭐
# =================================================
st.divider()
st.subheader("📦 My Request Status")

conn = connect_db()
cursor = conn.cursor()

requests = cursor.execute("""
SELECT r.request_id,
       f.Food_Name,
       r.quantity_requested,
       r.status,
       u.name as donor_name
FROM requests r
JOIN food_listings f ON r.food_id = f.Food_ID
JOIN users u ON r.donor_id = u.id
WHERE r.recipient_id=?
ORDER BY r.request_time DESC
""", (receiver_id,)).fetchall()

conn.close()

if requests:

    pending = [r for r in requests if r[3] == "PENDING"]
    approved = [r for r in requests if r[3] == "APPROVED"]
    rejected = [r for r in requests if r[3] == "REJECTED"]

    if pending:
        st.markdown("### 🟡 Pending Requests")
        st.dataframe(pending)

    if approved:
        st.markdown("### 🟢 Approved Requests")
        st.dataframe(approved)

    if rejected:
        st.markdown("### 🔴 Rejected Requests")
        st.dataframe(rejected)

else:
    st.info("No requests made yet.")