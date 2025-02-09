from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

# Load trained model
model = joblib.load("best_model.pkl")

# Load label encoders (if they were saved)
try:
    encoders = joblib.load("label_encoders.pkl")
except:
    encoders = {}  # If encoders are missing, handle dynamically

# Define expected features
expected_features = [
    "type", "departure_delay", "arrival_iataCode", "arrival_gate", 
    "airline_iataCode", "flight_number", "codeshared_airline_iataCode", 
    "codeshared_flight_number", "scheduled_vs_actual_departure"
]

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input JSON data
        data = request.get_json()

        # Compute departure delay from timestamps
        try:
            scheduled_departure = datetime.fromisoformat(data["scheduled_departure"])
            actual_departure = datetime.fromisoformat(data["actual_departure"])
            departure_delay = (actual_departure - scheduled_departure).total_seconds() / 60
        except:
            departure_delay = 0  

        # Compute scheduled vs actual departure delay
        try:
            scheduled_runway = datetime.fromisoformat(data["scheduled_runway"])
            actual_runway = datetime.fromisoformat(data["actual_runway"])
            scheduled_vs_actual_departure = (actual_runway - scheduled_runway).total_seconds() / 60
        except:
            scheduled_vs_actual_departure = 0  

        # Create DataFrame with raw input
        df = pd.DataFrame([{
            "type": data.get("type", "commercial"),
            "departure_delay": departure_delay,  
            "arrival_iataCode": data.get("arrival_iataCode", ""),
            "arrival_gate": data.get("arrival_gate", ""),
            "airline_iataCode": data.get("airline_iataCode", ""),
            "flight_number": data.get("flight_number", ""),
            "codeshared_airline_iataCode": data.get("codeshared_airline_iataCode", ""),
            "codeshared_flight_number": data.get("codeshared_flight_number", ""),
            "scheduled_vs_actual_departure": scheduled_vs_actual_departure  
        }])

        # **Apply Label Encoding for Categorical Features**
        for col in df.select_dtypes(include=['object']).columns:
            if col in encoders:
                df[col] = df[col].map(lambda x: encoders[col].transform([x])[0] if x in encoders[col].classes_ else -1)
            else:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col])
                encoders[col] = le  

        # Convert numerical features to float
        for feature in ["departure_delay", "scheduled_vs_actual_departure"]:
            df[feature] = pd.to_numeric(df[feature], errors="coerce").fillna(0)

        # Ensure only the required features are kept
        df = df[expected_features]

        # **Log Processed Data for Debugging**
        print("Final Processed Input for Model:\n", df)
        print("Processed Data Types:\n", df.dtypes)
        

        # **Make Prediction**
        prediction = model.predict(df)
        probabilities = model.predict_proba(df)  

        return jsonify({
            "prediction": int(prediction[0]),
            "confidence": probabilities.tolist()
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
