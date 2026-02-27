import sqlite3
import pandas as pd
import bcrypt
import os

# ------------------------------------------------
# ALWAYS USE ABSOLUTE PATH
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "food_donation.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ------------------------------------------------
# DROP TABLES (prevents column errors)
# ------------------------------------------------
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS food_listings")


# ------------------------------------------------
# USERS TABLE
# ------------------------------------------------
cursor.execute("""
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    city TEXT,
    lat REAL,
    lon REAL
)
""")


# ------------------------------------------------
# FOOD LISTINGS TABLE (UPDATED FOR ML + GEO)
# ------------------------------------------------
cursor.execute("""
CREATE TABLE food_listings(
    Food_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Food_Name TEXT,
    Quantity INTEGER,
    Location TEXT,
    Provider_Type TEXT,
    Provider_ID INTEGER,
    lat REAL,
    lon REAL,
    Expiry_Date TEXT,
    days_to_expiry INTEGER,
    Safety_Status TEXT
)
""")


# ------------------------------------------------
# CREATE ADMIN
# ------------------------------------------------
admin_password = bcrypt.hashpw(
    "admin123".encode(),
    bcrypt.gensalt()
).decode()

cursor.execute("""
INSERT INTO users
(name, email, password, role, city, lat, lon)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "Admin",
    "admin@food.com",
    admin_password,
    "Admin",
    "Hyderabad",
    17.3850,
    78.4867
))


# ------------------------------------------------
# LOAD INITIAL FOOD DATA (OPTIONAL BUT GOOD)
# Adds realistic demo data for professors
# ------------------------------------------------
csv_path = os.path.join(BASE_DIR, "Data", "food_listings_data.csv")

if os.path.exists(csv_path):

    df = pd.read_csv(csv_path)

    # Ensure required columns exist
    needed_cols = [
        "Food_Name",
        "Quantity",
        "Location",
        "Provider_Type"
    ]

    df = df[needed_cols]

    # Add ML columns
    df["Provider_ID"] = 1
    df["lat"] = 17.3850
    df["lon"] = 78.4867
    df["Expiry_Date"] = "2025-12-31"
    df["days_to_expiry"] = 10
    df["Safety_Status"] = "SAFE ✅"

    df.to_sql(
        "food_listings",
        conn,
        if_exists="append",
        index=False
    )


# ------------------------------------------------
conn.commit()
conn.close()

print("✅ DATABASE CREATED SUCCESSFULLY WITH ADMIN + ML READY TABLES")
