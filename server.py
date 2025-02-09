from flask import Flask, jsonify, request, render_template
import requests
from google.cloud import bigquery
from dotenv import load_dotenv
from flask_cors import CORS
import os
import joblib
import pickle
import pandas as pd

app = Flask(__name__)
CORS(app) 

# Load environment variables from .env file
load_dotenv()


import joblib

try:
    model = joblib.load("best_model.pkl", mmap_mode="r")  # Try loading with memory mapping
    print("Model loaded successfully:", type(model))
except Exception as e:
    print("Error loading model:", str(e))


@app.route('/makeprediction', methods=['POST'])
def query():
    try:
        data = request.get_json()
        flight_number = data.get('flightNumber')
        airline_name = data.get('airlineName')
        departure_delay = data.get('departure_delay')
        scheduled_departure = data.get('scheduled_departure')
        actual_departure = data.get('actual_departure')
        departure_code = data.get('departure_code')

        if not flight_number or not airline_name:
            return jsonify({"message": "Flight number and airline name are required!"}), 400
        
        return jsonify({"message": 0}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/predictold')
def index6():
    return render_template('prediction.html') 


# Prediction using Gradient Boosting ML Model
@app.route('/predictnew', methods=['POST'])
def predict():
    try:
        # Get JSON data from request
        data = request.get_json()

        # Debugging: Print input data type
        print("Received data:", data)

        # Convert JSON data into a pandas DataFrame
        df = pd.DataFrame([data])

        # Debugging: Print DataFrame to check formatting
        print("DataFrame structure:\n", df)

        # Ensure the model has a predict method
        if not hasattr(model, "predict"):
            return jsonify({"error": "Model is not properly loaded"}), 500

        # Make prediction
        prediction = model.predict(df)

        # Debugging: Print prediction result
        print("Prediction:", prediction)

        # Return prediction as JSON response
        result = {"prediction": int(prediction[0])}
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
