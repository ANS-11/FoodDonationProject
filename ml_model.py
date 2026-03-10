import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib

print("Loading dataset...")

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
df = pd.read_csv("Data/food_listings_data.csv")

df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'], errors='coerce')
df = df.dropna(subset=['Expiry_Date'])

reference_date = pd.Timestamp("2025-03-01")

df['days_to_expiry'] = (
    df['Expiry_Date'] - reference_date
).dt.total_seconds() / (60 * 60 * 24)

df = df.dropna(subset=['days_to_expiry'])

# ------------------------------------------------
# CREATE SAFETY LABEL
# ------------------------------------------------
# Food is safe if expiry > 2 days and quantity > 5
df['safe'] = np.where(
    (df['days_to_expiry'] > 2) & (df['Quantity'] > 5),
    1,
    0
)

print("\nInitial Class Distribution:")
print(df['safe'].value_counts())

# ------------------------------------------------
# BALANCE DATASET
# ------------------------------------------------
safe_df = df[df['safe'] == 1]
unsafe_df = df[df['safe'] == 0]

# Balance classes
min_size = min(len(safe_df), len(unsafe_df))

safe_df = safe_df.sample(min_size, random_state=42)
unsafe_df = unsafe_df.sample(min_size, random_state=42)

df = pd.concat([safe_df, unsafe_df])

print("\nBalanced Class Distribution:")
print(df['safe'].value_counts())

# ------------------------------------------------
# FEATURES
# ------------------------------------------------
X = df[['Quantity', 'days_to_expiry']]
y = df['safe']

# ------------------------------------------------
# SCALE FEATURES
# ------------------------------------------------
scaler = StandardScaler()
X = scaler.fit_transform(X)

# ------------------------------------------------
# TRAIN TEST SPLIT
# ------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining Logistic Regression model...")

# ------------------------------------------------
# TRAIN MODEL
# ------------------------------------------------
model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced'
)

model.fit(X_train, y_train)

# ------------------------------------------------
# MODEL EVALUATION
# ------------------------------------------------
pred = model.predict(X_test)

accuracy = accuracy_score(y_test, pred) * 100

print(f"\nModel Accuracy: {accuracy:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, pred, zero_division=0))

# ------------------------------------------------
# SAVE MODEL
# ------------------------------------------------
joblib.dump(model, "food_safety_model.pkl")

print("\nModel saved successfully as food_safety_model.pkl")