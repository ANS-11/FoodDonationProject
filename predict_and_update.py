import sqlite3
import joblib
import pandas as pd

print("Loading trained model...")

# ✅ Load model
model = joblib.load("food_safety_model.pkl")

print("Connecting to database...")

# ⚠️ MAKE SURE NAME MATCHES YOUR DB EXACTLY
conn = sqlite3.connect("food_donation.db")

# -----------------------------
# LOAD DATA
# -----------------------------
query = """
SELECT Food_ID, Quantity, Expiry_Date
FROM food_listings
"""

df = pd.read_sql_query(query, conn)

print("Cleaning expiry dates...")

# Convert safely (prevents crashes)
df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'], errors='coerce')

# Drop corrupted rows
df = df.dropna(subset=['Expiry_Date'])

# -----------------------------
# CALCULATE DAYS
# -----------------------------
today = pd.Timestamp.today()

df['days_to_expiry'] = (df['Expiry_Date'] - today).dt.days

# -----------------------------
# PREDICT
# -----------------------------
print("Running ML predictions...")

features = df[['Quantity', 'days_to_expiry']]
df['prediction'] = model.predict(features)

# Convert numeric → label
df['prediction'] = model.predict(features)

df['prediction'] = (
    pd.Series(df['prediction'])
    .map({1: "SAFE", 0: "UNSAFE"})
    .astype(str)
    .str.strip()
    .str.replace(r'[^A-Z]', '', regex=True)  # removes ticks, emojis, garbage
)


# -----------------------------
# SAFETY OVERRIDE (VERY IMPORTANT)
# -----------------------------
df.loc[df['days_to_expiry'] < 0, 'prediction'] = "UNSAFE"

# -----------------------------
# UPDATE DATABASE
# -----------------------------
cursor = conn.cursor()

print("Updating database...")

for _, row in df.iterrows():
    cursor.execute("""
        UPDATE food_listings
        SET Safety_Status = ?,
            days_to_expiry = ?
        WHERE Food_ID = ?
    """, (
        row['prediction'],
        int(row['days_to_expiry']),
        row['Food_ID']
    ))

conn.commit()
conn.close()

print("\n✅ SUCCESS! Database updated with ML predictions.")
