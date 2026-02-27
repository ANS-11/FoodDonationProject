import pandas as pd
from geopy.distance import geodesic
import streamlit as st
from auth_db import connect_db
import joblib


# =====================================================
# LOAD ML MODEL ONLY ONCE
# =====================================================
@st.cache_resource
def load_model():
    return joblib.load("food_safety_model.pkl")


model = load_model()

MAX_DISTANCE_KM = 200


# =====================================================
# GET RECEIVER INFO
# =====================================================
def get_receiver(user_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, city, lat, lon
        FROM users
        WHERE id=?
    """, (user_id,))

    receiver = cursor.fetchone()

    return receiver


# =====================================================
# MAIN RECOMMENDER
# =====================================================
def recommend_food(user_id, food_requested, quantity_needed):

    receiver = get_receiver(user_id)

    if receiver is None:
        return None, pd.DataFrame()

    name, city, r_lat, r_lon = receiver

    if r_lat is None or r_lon is None:
        return receiver, pd.DataFrame()

    receiver_coords = (r_lat, r_lon)

    # ------------------------------------------------
    # LOAD FOOD LISTINGS
    # ------------------------------------------------
    conn = connect_db()

    df = pd.read_sql("""
        SELECT *
        FROM food_listings
        WHERE Quantity > 0
    """, conn)

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # EXPIRY FILTER
    # ------------------------------------------------
    df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'])

    today = pd.Timestamp.now()

    df['days_to_expiry'] = (
        df['Expiry_Date'] - today
    ).dt.days

    df = df[df['days_to_expiry'] > 0]

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # ML SAFETY PREDICTION
    # ------------------------------------------------
    features = df[['Quantity', 'days_to_expiry']]

    df['safe'] = model.predict(features)

    df = df[df['safe'] == 1]

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # FOOD MATCH
    # ------------------------------------------------
    food_requested = food_requested.lower().strip()

    df = df[
        df['Food_Name'].str.lower().str.strip()
        == food_requested
    ]

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # QUANTITY FILTER
    # ------------------------------------------------
    df = df[df['Quantity'] >= quantity_needed]

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # DISTANCE CALCULATION
    # ------------------------------------------------
    df = df.dropna(subset=['lat', 'lon'])

    distances = []

    for _, row in df.iterrows():
        distance = geodesic(
            receiver_coords,
            (row['lat'], row['lon'])
        ).km

        distances.append(distance)

    df['distance_km'] = distances

    df = df[df['distance_km'] <= MAX_DISTANCE_KM]

    if df.empty:
        return receiver, pd.DataFrame()

    # ------------------------------------------------
    # SMART RANKING
    # ------------------------------------------------
    df['score'] = (
        (0.7 * df['distance_km'])
        - (0.3 * df['Quantity'])
    )

    nearest = df.sort_values('score').head(5)

    return receiver, nearest