import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Create models folder
os.makedirs("models", exist_ok=True)

# Load dataset
df = pd.read_csv("data1.csv")

# Separate features and target
X = df.drop("label", axis=1)
y = df["label"]

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y.astype(str))

# ================= FIXED PART START =================

# Encode categorical feature columns
for col in X.columns:
    if X[col].dtype == "object":
        X[col] = LabelEncoder().fit_transform(X[col].astype(str))

# Force everything to numeric
X = X.apply(pd.to_numeric, errors="coerce")

# Fill ALL missing values
X = X.fillna(0)

# ================= FIXED PART END =================

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# Train Random Forest model
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Save model and label encoder
joblib.dump(model, "models/crop_model.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")

print("✅ Crop Recommendation Model Trained Successfully")

