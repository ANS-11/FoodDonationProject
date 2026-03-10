import pandas as pd
from geopy.distance import geodesic
import streamlit as st
from auth_db import connect_db
import joblib
import time

@st.cache_resource
def load_model():
    return joblib.load("food_safety_model.pkl")

model = load_model()

MAX_DISTANCE_KM = 200


def get_receiver(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, city, lat, lon
        FROM users
        WHERE id=?
    """, (user_id,))

    receiver = cursor.fetchone()
    conn.close()
    return receiver


def recommend_food(user_id, food_requested, quantity_needed):

    start_time = time.time()   # START TIMER

    receiver = get_receiver(user_id)

    if receiver is None:
        return None, pd.DataFrame()

    name, city, r_lat, r_lon = receiver

    if r_lat is None or r_lon is None:
        return receiver, pd.DataFrame()

    receiver_coords = (r_lat, r_lon)

    conn = connect_db()

    df = pd.read_sql("""
        SELECT *
        FROM food_listings
        WHERE Quantity > 0
    """, conn)

    conn.close()

    if df.empty:
        return receiver, pd.DataFrame()

    df['Expiry_Date'] = pd.to_datetime(
        df['Expiry_Date'],
        format='mixed',
        errors='coerce'
    )

    df = df.dropna(subset=['Expiry_Date'])

    current_time = pd.Timestamp.now()

    df = df[df['Expiry_Date'] > current_time]

    if df.empty:
        return receiver, pd.DataFrame()

    df['days_to_expiry'] = (
        (df['Expiry_Date'] - current_time)
        .dt.total_seconds() / (60 * 60 * 24)
    )

    # ML Prediction
    features = df[['Quantity', 'days_to_expiry']]
    probabilities = model.predict_proba(features)[:, 1]

    df['safe_probability'] = probabilities
    df = df[df['safe_probability'] > 0.5]

    if df.empty:
        return receiver, pd.DataFrame()

    food_requested = food_requested.lower().strip()

    df = df[
        df['Food_Name'].str.lower().str.strip()
        == food_requested
    ]

    if df.empty:
        return receiver, pd.DataFrame()

    df = df[df['Quantity'] >= quantity_needed]

    if df.empty:
        return receiver, pd.DataFrame()

    df = df.dropna(subset=['lat', 'lon'])

    df['distance_km'] = df.apply(
        lambda row: geodesic(
            receiver_coords,
            (row['lat'], row['lon'])
        ).km,
        axis=1
    )

    df = df[df['distance_km'] <= MAX_DISTANCE_KM]

    if df.empty:
        return receiver, pd.DataFrame()

    # Ranking
    df['score'] = (0.7 * df['distance_km']) - (0.3 * df['Quantity'])

    nearest = df.sort_values('score').head(5)

    end_time = time.time()   # END TIMER
    print("Recommendation Response Time:", round(end_time - start_time, 3), "seconds")

    return receiver, nearest