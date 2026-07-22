from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# ------------------------------------
# 1. LOAD DATASETS (SAFE LOAD)
# ------------------------------------
try:
    crop_df = pd.read_csv("data1000_generated.csv")
    market_df = pd.read_csv("marketdata.csv")
    history_df = pd.read_csv("pricehisy.csv")
except Exception as e:
    print("CSV loading error:", e)
    raise

# Convert all column names to lowercase
# Normalize column names: lowercase and strip whitespace
crop_df.columns = crop_df.columns.str.lower().str.strip()
market_df.columns = market_df.columns.str.lower().str.strip()
history_df.columns = history_df.columns.str.lower().str.strip()

# Convert date column safely
if "date" in history_df.columns:
    history_df["date"] = pd.to_datetime(history_df["date"], errors="coerce")

#/*range function is used*/
def parse_date(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed if pd.notna(parsed) else None


def format_history(df):
    rows = []
    for _, row in df.iterrows():
        date_value = row.get("date")
        rows.append({
            "crop": str(row.get("crop", "")),
            "date": date_value.strftime("%Y-%m-%d") if pd.notna(date_value) else None,
            "price": float(row.get("price", 0)) if pd.notna(row.get("price")) else None
        })
    return rows

# ------------------------------------
# 2. TRAIN CROP MODEL
# ------------------------------------
# Expected numeric feature columns (lowercase)
feature_cols = ["n", "p", "k", "temperature", "humidity", "ph", "rainfall"]

# Ensure features exist in the CSV
df_cols = [c.strip().lower() for c in crop_df.columns]
missing_features = [c for c in feature_cols if c not in df_cols]
if missing_features:
    raise RuntimeError(f"Missing expected crop feature columns: {missing_features}")

# Determine label column. Prefer an explicit 'label' column, otherwise try common alternatives
label_col = None
if "label" in df_cols:
    label_col = "label"
else:
    candidates = [c for c in df_cols if c not in feature_cols and c not in ("id", "date")]
    # prefer names containing these keywords
    for key in ("label", "crop", "target", "recommend", "recommended", "yield"):
        for c in candidates:
            if key in c:
                label_col = c
                break
        if label_col:
            break
    # fallback to first candidate if none matched
    if not label_col and candidates:
        label_col = candidates[0]

if not label_col:
    raise RuntimeError("Could not determine label column in data1000.csv. Found columns: %s" % ",".join(df_cols))

X_crop = crop_df[feature_cols].astype(float)
y_crop = crop_df[label_col]

crop_model = DecisionTreeClassifier(random_state=42)
crop_model.fit(X_crop, y_crop)

# ------------------------------------
# 3. FLASK SETUP
# ------------------------------------
app = Flask(__name__)
CORS(app)

# User storage file
USERS_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def generate_token():
    """Generate a unique token"""
    return secrets.token_hex(32)

# ------------------------------------
# 3a. LOGIN & REGISTER ROUTES
# ------------------------------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not name or not email or not password:
            return jsonify({"error": "Name, email, and password are required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        users = load_users()
        
        if email in users:
            return jsonify({"error": "Email already registered"}), 400
        
        # Store user with hashed password
        users[email] = {
            "name": name,
            "password": generate_password_hash(password),
            "created_at": datetime.now().isoformat()
        }
        
        save_users(users)
        
        # Generate token for auto-login
        token = generate_token()
        
        return jsonify({
            "message": "Registration successful",
            "token": token,
            "name": name
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        login_name = data.get("name", "").strip()
        password = data.get("password", "")
        
        if not (email or login_name) or not password:
            return jsonify({"error": "Name/email and password are required"}), 400
        
        users = load_users()
        user = None
        user_email = None
        
        if email:
            user = users.get(email)
            user_email = email
        elif login_name:
            matches = [(e, u) for e, u in users.items() if u.get("name", "").strip().lower() == login_name.lower()]
            if len(matches) == 1:
                user_email, user = matches[0]
            elif len(matches) > 1:
                return jsonify({"error": "Multiple users found with that name. Please use email."}), 400
        
        if not user:
            return jsonify({"error": "Invalid name/email or password"}), 401
        
        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid name/email or password"}), 401
        
        token = generate_token()
        
        response = {
            "message": "Login successful",
            "token": token,
            "name": user["name"]
        }
        if user_email:
            response["email"] = user_email
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------------
# 4. CROP PREDICTION API
# ------------------------------------
@app.route("/predict-crop", methods=["POST"])
def predict_crop():
    try:
        data = request.get_json()

        features = [[
            float(data.get("nitrogen", 0)),
            float(data.get("phosphorus", 0)),
            float(data.get("potassium", 0)),
            float(data.get("temperature", 0)),
            float(data.get("humidity", 0)),
            float(data.get("ph", 0)),
            float(data.get("rainfall", 0))
        ]]

        crop = crop_model.predict(features)[0]

        return jsonify({
            "recommended_crop": crop,
            "confidence": 0.95
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# 5. CURRENT MARKET PRICE API (FIXED)
# ------------------------------------
@app.route("/get-current-price", methods=["POST"])
def get_current_price():
    try:
        data = request.get_json()
        crop = str(data.get("crop", "")).lower().strip()

        # Optional filters
        state = str(data.get("state", "")).strip()
        market = str(data.get("market", "")).strip()

        if crop == "":
            return jsonify({"error": "Crop is required"}), 400

        # check columns exist
        required = ["crop", "price", "market", "state", "date"]
        for col in required:
            if col not in market_df.columns:
                return jsonify({"error": f"{col} column missing in CSV"}), 500

        # search crop
        result = market_df[
            market_df["crop"].astype(str).str.lower().str.strip() == crop
        ]

        # apply optional state/market filters if provided
        if state:
            state_lower = state.lower()
            state_filtered = result[result["state"].astype(str).str.lower().str.strip() == state_lower]
            if not state_filtered.empty:
                result = state_filtered
        if market:
            market_lower = market.lower()
            market_filtered = result[result["market"].astype(str).str.lower().str.strip() == market_lower]
            if not market_filtered.empty:
                result = market_filtered

        if result.empty:
            return jsonify({"error": "Crop not found"}), 404

        row = result.iloc[0]

        return jsonify({
            "crop": str(row["crop"]),
            "price": float(row["price"]),
            "market": str(row["market"]),
            "state": str(row.get("state", "")),
            "date": str(row["date"])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# 6. PRICE PREDICTION API
# ------------------------------------
@app.route("/predict-price", methods=["POST"])
def predict_price():
    try:
        data = request.get_json()
        crop = str(data.get("crop", "")).lower()
        days = int(data.get("days", 7))
        period = str(data.get("period", "days")).lower()
        include_history = data.get("include_history", False)
        start_year = data.get("start_year", None)
        end_year = data.get("end_year", None)

        if crop == "":
            return jsonify({"error": "Crop required"}), 400

        crop_history = history_df[
            history_df["crop"].astype(str).str.lower() == crop
        ]

        if crop_history.empty:
            return jsonify({"error": "Crop history not found"}), 404

        crop_history = crop_history.sort_values("date")

        # If yearly prediction requested, convert dates to fractional years since min date
        if period == "years":
            min_date = crop_history["date"].min()
            # fractional years since min_date
            crop_history["year_number"] = (crop_history["date"] - min_date).dt.days / 365.25

            X = crop_history[["year_number"]].astype(float)
            y = crop_history["price"]

            model = LinearRegression()
            model.fit(X, y)

            all_dates = []
            all_prices = []

            # If start_year and end_year provided, use those; otherwise use historical + days
            if start_year and end_year:
                # Generate data for each year in range
                for year in range(start_year, end_year + 1):
                    # Estimate year_number for this year relative to min_date
                    year_date = pd.Timestamp(f'{year}-01-01')
                    year_num = (year_date - min_date).days / 365.25
                    
                    if year_num < 0:
                        # Historical year - try to get actual data if available
                        hist_data = crop_history[crop_history["date"].dt.year == year]
                        if not hist_data.empty:
                            avg_price = hist_data["price"].mean()
                            all_prices.append(round(float(avg_price), 2))
                        else:
                            # Predict for historical year
                            predicted_price = model.predict([[year_num]])[0]
                            all_prices.append(round(float(predicted_price), 2))
                    else:
                        # Future or current year - predict
                        predicted_price = model.predict([[year_num]])[0]
                        all_prices.append(round(float(predicted_price), 2))
                    
                    all_dates.append(str(year))
            else:
                # Include historical data if requested
                if include_history:
                    max_date = crop_history["date"].max()
                    cutoff_date = max_date - timedelta(days=365*3)
                    historical = crop_history[crop_history["date"] >= cutoff_date]
                    
                    for _, row in historical.iterrows():
                        year_label = row["date"].year
                        all_dates.append(str(year_label))
                        all_prices.append(round(float(row["price"]), 2))

                last_year_num = float(crop_history["year_number"].max())
                last_year_label = crop_history["date"].max().year
                
                for i in range(1, days + 1):
                    next_year_num = last_year_num + i
                    predicted_price = model.predict([[next_year_num]])[0]

                    all_dates.append(str(last_year_label + i))
                    all_prices.append(round(float(predicted_price), 2))

            return jsonify({
                "dates": all_dates,
                "prices": all_prices
            })

        # Default: days-based (daily) prediction
        crop_history["day_number"] = (
            crop_history["date"] - crop_history["date"].min()
        ).dt.days

        X = crop_history[["day_number"]]
        y = crop_history["price"]

        model = LinearRegression()
        model.fit(X, y)

        last_day = crop_history["day_number"].max()
        future_dates = []
        future_prices = []

        for i in range(1, days + 1):
            next_day = last_day + i
            predicted_price = model.predict([[next_day]])[0]

            future_dates.append(
                (crop_history["date"].max() + timedelta(days=i)).strftime("%d-%m-%Y")
            )
            future_prices.append(round(float(predicted_price), 2))

        return jsonify({
            "dates": future_dates,
            "prices": future_prices
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# 7. PROFIT ESTIMATION API
# ------------------------------------
@app.route("/estimate-profit", methods=["POST"])
def estimate_profit():
    try:
        data = request.get_json()

        price = float(data.get("price", 0))
        yield_amount = float(data.get("yield_amount", 0))
        fertilizer_cost = float(data.get("fertilizer_cost", 0))
        irrigation_cost = float(data.get("irrigation_cost", 0))

        revenue = price * yield_amount
        cost = fertilizer_cost + irrigation_cost
        profit = revenue - cost

        return jsonify({
            "expected_profit": round(profit, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# RUN SERVER
# ------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)