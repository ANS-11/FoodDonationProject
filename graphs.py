import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# connect database
conn = sqlite3.connect("food_donation.db")

# read table
df = pd.read_sql("SELECT * FROM food_listings", conn)

# ----------------------------
# Graph 1: Safe vs Unsafe
# ----------------------------
df['Safety_Status'].value_counts().plot(kind='bar')
plt.title("Safe vs Unsafe Food")
plt.xlabel("Safety Status")
plt.ylabel("Count")
plt.show()


# ----------------------------
# Graph 2: Provider Type
# ----------------------------
df['Provider_Type'].value_counts().plot(kind='bar')
plt.title("Food Providers Distribution")
plt.xlabel("Provider Type")
plt.ylabel("Count")
plt.show()


# ----------------------------
# Graph 3: Days to Expiry
# ----------------------------
plt.hist(df['days_to_expiry'], bins=5)
plt.title("Food Expiry Distribution")
plt.xlabel("Days to Expiry")
plt.ylabel("Number of Foods")
plt.show()