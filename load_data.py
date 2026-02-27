import pandas as pd

# Load dataset
file_path = "Data/food_listings_data.csv"

df = pd.read_csv(file_path)

# Show first 5 rows
print(df.head())

# Show dataset info
print("\nDataset Info:\n")
print(df.info())
