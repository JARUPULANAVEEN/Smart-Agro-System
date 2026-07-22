import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# Create models folder
os.makedirs("models", exist_ok=True)

# Load dataset safely
data = pd.read_csv("data2.csv")
data.columns = data.columns.str.strip()

# Ensure price column exists
if "price" not in data.columns:
    raise KeyError(f"❌ 'price' column not found. Found columns: {data.columns.tolist()}")

# Ensure price column is numeric
data["price"] = pd.to_numeric(data["price"], errors="coerce")
data = data.dropna(subset=["price"])

# ✅ AUTO-ADJUST SEQUENCE LENGTH (NO ERROR)
SEQ_LEN = min(30, len(data) - 1)

# Convert to numpy array
prices = data["price"].values.reshape(-1, 1)

# Scale data
scaler = MinMaxScaler()
scaled_prices = scaler.fit_transform(prices)

# Create sequences
X, y = [], []
for i in range(SEQ_LEN, len(scaled_prices)):
    X.append(scaled_prices[i - SEQ_LEN:i])
    y.append(scaled_prices[i])

X = np.array(X)
y = np.array(y).reshape(-1, 1)

# Build LSTM model
model = Sequential([
    Input(shape=(SEQ_LEN, 1)),
    LSTM(64, return_sequences=True),
    LSTM(64),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

# Train model
model.fit(X, y, epochs=10, batch_size=16, verbose=1)

# Save model & scaler
model.save("models/price_lstm.h5")
joblib.dump(scaler, "models/price_scaler.pkl")

print("✅ Price Prediction LSTM Model Trained Successfully")


