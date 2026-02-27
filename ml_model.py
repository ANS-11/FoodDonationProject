import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

print("Loading dataset...")

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
df = pd.read_csv("Data/food_listings_data.csv")

# ------------------------------------------------
# STEP 1 — Convert Expiry Date
# ------------------------------------------------
df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'], errors='coerce')
df = df.dropna(subset=['Expiry_Date'])

# Use fixed reference date
today = pd.Timestamp("2025-03-20")

df['days_to_expiry'] = (df['Expiry_Date'] - today).dt.days

# ------------------------------------------------
# STEP 2 — CREATE REALISTIC SAFETY LABEL
# ------------------------------------------------
# Instead of deterministic rule, use probability

np.random.seed(42)

# Sigmoid function to convert days_to_expiry into probability
probability_safe = 1 / (1 + np.exp(-0.8 * df['days_to_expiry']))

random_values = np.random.rand(len(df))

df['safe'] = np.where(random_values < probability_safe, 1, 0)

print("\nClass Distribution:")
print(df['safe'].value_counts())

# Ensure at least 2 classes
if df['safe'].nunique() < 2:
    raise ValueError("Dataset has only ONE class after labeling.")

# ------------------------------------------------
# STEP 3 — Feature Selection
# ------------------------------------------------
features = ['Quantity', 'days_to_expiry']

X = df[features]
y = df['safe']

# ------------------------------------------------
# STEP 4 — Train/Test Split
# ------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ------------------------------------------------
# STEP 5 — Train Model
# ------------------------------------------------
print("\nTraining Logistic Regression model...")

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# ------------------------------------------------
# STEP 6 — Evaluate
# ------------------------------------------------
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"\nModel Accuracy: {accuracy*100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, predictions))

# ------------------------------------------------
# STEP 7 — Save Model
# ------------------------------------------------
joblib.dump(model, "food_safety_model.pkl")

print("\n✅ Model saved as food_safety_model.pkl")
print("READY to plug into your food donation app 🚀")
