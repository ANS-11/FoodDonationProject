import streamlit as st
from email_utils import send_email
from recommend_food import recommend_food
from auth_db import connect_db
from datetime import datetime, timedelta

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
# BLOCKED DONORS (FOOD SPECIFIC)
# ------------------------------------------------
def get_blocked_donors(receiver_id, food_id):
    conn = connect_db()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT donor_id FROM requests
        WHERE recipient_id = ?
        AND food_id = ?
        AND status IN ('REJECTED','EXPIRED')
    """, (receiver_id, food_id)).fetchall()

    conn.close()
    return {r[0] for r in rows}

# ------------------------------------------------
# SAFE FOOD LIST (FIXED ✅)
# ------------------------------------------------
@st.cache_data(ttl=20)
def get_safe_foods():
    conn = connect_db()
    cursor = conn.cursor()

    current_date = datetime.now().strftime("%Y-%m-%d")

    foods = cursor.execute("""
        SELECT DISTINCT Food_Name
        FROM food_listings
        WHERE Safety_Status='SAFE'
        AND Quantity > 0
        AND Expiry_Date > ?
    """, (current_date,)).fetchall()

    conn.close()
    return [f[0] for f in foods]

foods = get_safe_foods()

if not foods:
    st.warning("⚠️ No fresh and available food items right now.")
    st.stop()

food_type = st.selectbox("Food Type Needed", foods)

# ------------------------------------------------
# FIND DONOR
# ------------------------------------------------
if st.button("Find Nearest Safe Donor"):

    with st.spinner("🔎 Searching nearby safe donors..."):
        receiver, results = recommend_food(receiver_id, food_type, 1)

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

        filtered_results = []

        for _, row in results.iterrows():

            blocked = get_blocked_donors(receiver_id, row['Food_ID'])

            if row['Provider_ID'] not in blocked:
                filtered_results.append(row)

        if not filtered_results:
            st.warning("⚠️ Previous donors didn’t respond. Showing new donors if available.")
        else:
            for row in sorted(filtered_results, key=lambda x: x['distance_km']):

                st.write("------")
                st.write(f"🍲 **Food:** {row['Food_Name']}")
                st.write(f"📦 Quantity Available: {row['Quantity']}")
                st.write(f"🏪 Provider: {row['Provider_Type']}")
                st.write(f"📍 Distance: {round(row['distance_km'],2)} km")

                st.caption("⚡ Donor should respond within 15 minutes or request will expire")

                request_qty = st.number_input(
                    "Request quantity",
                    min_value=1,
                    max_value=int(row['Quantity']),
                    key=f"qty_{row['Food_ID']}"
                )

                if st.button("Send Request", key=f"req_{row['Food_ID']}"):

                    st.info("⏳ Waiting for donor response (max 15 mins)...")

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
                         quantity_requested, status, request_time)
                        VALUES (?, ?, ?, ?, 'PENDING', ?)
                    """, (
                        row['Food_ID'],
                        donor_id,
                        receiver_id,
                        request_qty,
                        datetime.now().isoformat()
                    ))

                    conn.commit()
                    conn.close()

                    st.cache_data.clear()
                    st.session_state.success_msg = "✅ Request sent successfully!"
                    st.rerun()

# ------------------------------------------------
# REQUEST STATUS
# ------------------------------------------------
st.divider()
st.subheader("📦 My Request Status")

conn = connect_db()
cursor = conn.cursor()

requests = cursor.execute("""
SELECT r.request_id,
       f.Food_Name,
       r.quantity_requested,
       r.status,
       u.name,
       r.request_time,
       r.food_id,
       r.donor_id
FROM requests r
JOIN food_listings f ON r.food_id = f.Food_ID
JOIN users u ON r.donor_id = u.id
WHERE r.recipient_id=?
ORDER BY r.request_time DESC
""", (receiver_id,)).fetchall()

conn.close()

updated_requests = []

for r in requests:
    request_id, food_name, qty, status, donor_name, req_time, food_id, donor_id = r

    if status == "PENDING":
        req_time = datetime.fromisoformat(req_time)

        if datetime.now() - req_time > timedelta(minutes=15):

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE requests
                SET status='EXPIRED'
                WHERE request_id=?
            """, (request_id,))
            conn.commit()
            conn.close()

            status = "EXPIRED"

    updated_requests.append((request_id, food_name, qty, status, donor_name, food_id))

pending = [r for r in updated_requests if r[3] == "PENDING"]
approved = [r for r in updated_requests if r[3] == "APPROVED"]
rejected = [r for r in updated_requests if r[3] == "REJECTED"]
expired = [r for r in updated_requests if r[3] == "EXPIRED"]

if pending:
    st.markdown("### 🟡 Pending Requests")
    st.dataframe(pending)

if approved:
    st.markdown("### 🟢 Approved Requests")
    st.dataframe(approved)

if rejected:
    st.markdown("### 🔴 Rejected Requests")
    st.dataframe(rejected)

if expired:
    st.markdown("### ⚫ Expired Requests")

    for r in expired:
        request_id, food_name, qty, status, donor_name, food_id = r

        st.write(f"🍲 {food_name} | Qty: {qty} | Donor: {donor_name}")
        st.error("❌ Request expired (no response from donor)")
        st.info("👉 Try searching again to find another donor.")

if not updated_requests:
    st.info("No requests made yet.")