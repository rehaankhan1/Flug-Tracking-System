from flask import Flask, jsonify, request, render_template
from selenium import webdriver
from collections import OrderedDict
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import redis
import threading
import time
import json
from google.cloud import bigquery
from dotenv import load_dotenv
import os
import joblib
import pickle
import pandas as pd

# import sklearn
# print(sklearn.__version__)  # Check the installed version



app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = True  # 👈 Critical configuration change

# import joblib

# try:
#     model = joblib.load("best_model.pkl", mmap_mode="r")  # Try loading with memory mapping
#     print("Model loaded successfully:", type(model))
# except Exception as e:
#     print("Error loading model:", str(e))



# Load environment variables from .env file
load_dotenv()
# export GOOGLE_APPLICATION_CREDENTIALS="C:\Users\Admin\Documents\Flug-system\route\static\flightmodelfra-a6ceade8480e.json"

#aerodatabox API https://api.market/store/aedbx/aerodatabox
API_KEY = "cm6b983hu0003jv03lg3eb62a"
BASE_URL = "https://api.magicapi.dev/api/v1/aedbx/aerodatabox/flights/Number/"

# Access the variable
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS1')
print(f"Using credentials from: {credentials_path}")

# redis-14349.c11.us-east-1-2.ec2.redns.redis-cloud.com:14349
# Configure Redis connection
redis_host = 'redis-19861.c278.us-east-1-4.ec2.redns.redis-cloud.com'
redis_port = 19861
redis_password = 'vwTQ74vjYwsFj0HsFyaTmlTYCs7jJAKN'

redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True
)



# ✅ Load trained ML model using pickle
try:
    with open("best_model.pkl", "rb") as file:
        model = pickle.load(file)

    if not hasattr(model, "predict"):
        raise TypeError("Loaded model does not have a 'predict' method. Ensure 'best_model.pkl' is a trained model!")

    print("✅ Model loaded successfully:", type(model))

except Exception as e:
    print("❌ Error loading model:", str(e))
    model = None

# ✅ Load categorical encoders using pickle
try:
    with open("encoder_model.pkl", "rb") as file:
        encoders = pickle.load(file)

    if not isinstance(encoders, dict) or len(encoders) == 0:
        raise ValueError("Encoders dictionary is empty or invalid!")

    print("✅ Encoders loaded successfully!")
    print("Available encoders:", list(encoders.keys()))

except Exception as e:
    print("❌ Error loading encoders:", str(e))
    encoders = None


### **Helper Function to Encode New Input**
def encode_new_input(data):
    """
    Encodes categorical inputs using saved encoders.
    Returns encoded data and an error message if an unknown category is encountered.
    """
    if encoders is None:
        return None, "❌ Error: Encoders not loaded."

    encoded_data = {}

    for col, encoder in encoders.items():
        if col in data:
            try:
                encoded_data[col] = encoder.transform([data[col]])[0]  # Encode value
            except ValueError:
                return None, f"❌ Error: Unknown category '{data[col]}' for '{col}'. Please provide a valid category."
        else:
            return None, f"❌ Error: Missing required field '{col}'."

    return encoded_data, None  # No errors



EUROPE_AREA = {
   "lamin": 47.270111,  
  "lomin": 5.866342,   
  "lamax": 55.058347,  
  "lomax": 15.041896   
}

WORLD_AREA = {
 "lamin": -90.0,  
  "lomin": -180.0, 
  "lamax": 90.0,   
  "lomax": 180.0   
}

def time_difference(time1: str, time2: str) -> float:
    format_str = "%H:%M"
    t1 = datetime.strptime(time1, format_str)
    t2 = datetime.strptime(time2, format_str)
    
    diff = abs(t1 - t2)
    return "{:.1f}".format(float(diff.seconds / 60))  # Return difference in minutes as float




def fetch_and_store_flights_world():
    username = 'likeaman21'
    password = 'mardhotoayesa21#'

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    while True:
        try:
            # Fetch flights from the OpenSky API with authentication
            response = requests.get('https://opensky-network.org/api/states/all', params={
                'lamin': WORLD_AREA['lamin'],
                'lomin': WORLD_AREA['lomin'],
                'lamax': WORLD_AREA['lamax'],
                'lomax': WORLD_AREA['lomax']
            }, 
            auth=(username, password),  # Adding basic auth
            headers=headers
            )
            response.raise_for_status()  # Raise an error for bad responses
            flights = response.json().get('states', [])

            if flights:
                all_flight_data = []  # List to store each flight's data

                for flight in flights:
                    # Unpack the relevant flight data
                    icao24 = flight[0]
                    timepos = flight[3]
                    destination = flight[2]
                    callsign = flight[1].strip() if flight[1] else None
                    longitude = flight[5]
                    latitude = flight[6]
                    velocity = flight[9] if len(flight) > 9 else None
                    heading = flight[10] if len(flight) > 10 else None

                    # Create a dictionary for the flight data
                    flight_data = {
                        "Flight": callsign,
                        "Time-pos": timepos,
                        "ICAO24": icao24,
                        "Destination": destination,
                        "latitude": latitude,
                        "longitude": longitude,
                        "Speed": f"{velocity} m/s" if velocity is not None else None,
                        "Heading": f"{heading}°" if heading is not None else None
                    }

                    # Append each flight's data to the list                   
                    all_flight_data.append(flight_data)
                    

                # Store the flight data in Redis
                redis_client.set('flights_data_world', str(all_flight_data))

            # Wait for 60 seconds before fetching again
            time.sleep(200000)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching flights: {str(e)}")
            time.sleep(300)  
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            time.sleep(300)  

def fetch_and_store_flights():
    username = 'likeaman21'
    password = 'mardhotoayesa21#'

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    while True:
        try:
            # Fetch flights from the OpenSky API with authentication
            response = requests.get('https://opensky-network.org/api/states/all', params={
                'lamin': EUROPE_AREA['lamin'],
                'lomin': EUROPE_AREA['lomin'],
                'lamax': EUROPE_AREA['lamax'],
                'lomax': EUROPE_AREA['lomax']
            }, 
            auth=(username, password),  # Adding basic auth
            headers=headers
            )
            response.raise_for_status()  # Raise an error for bad responses
            flights = response.json().get('states', [])

            if flights:
                all_flight_data = []  # List to store each flight's data

                for flight in flights:
                    # Unpack the relevant flight data
                    icao24 = flight[0]
                    timepos = flight[3]
                    destination = flight[2]
                    callsign = flight[1].strip() if flight[1] else None
                    longitude = flight[5]
                    latitude = flight[6]
                    velocity = flight[9] if len(flight) > 9 else None
                    heading = flight[10] if len(flight) > 10 else None

                    # Create a dictionary for the flight data
                    flight_data = {
                        "Flight": callsign,
                        "Time-pos": timepos,
                        "ICAO24": icao24,
                        "Destination": destination,
                        "latitude": latitude,
                        "longitude": longitude,
                        "Speed": f"{velocity} m/s" if velocity is not None else None,
                        "Heading": f"{heading}°" if heading is not None else None
                    }

                    # Append each flight's data to the list                   
                    all_flight_data.append(flight_data)
                    

                # Store the flight data in Redis
                redis_client.set('flights_data', str(all_flight_data))

            # Wait for 60 seconds before fetching again
            time.sleep(200)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching flights: {str(e)}")
            time.sleep(300)  
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            time.sleep(300)  

# Start the background thread
threading.Thread(target=fetch_and_store_flights, daemon=True).start()
threading.Thread(target=fetch_and_store_flights_world, daemon=True).start()

@app.route('/track', methods=['GET'])
def get_track():
    # Get the icao24 parameter from the user
    icao24 = request.args.get('icao24')
    if not icao24:
        return jsonify({"error": "icao24 parameter is required"}), 400

    # OpenSky Network API endpoint
    url = f"https://opensky-network.org/api/tracks/all?icao24={icao24}&time=0"

    try:
        # Make a request to the OpenSky API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Return the JSON response
        return jsonify(response.json())

    except requests.RequestException as e:
        # Handle any errors from the OpenSky API request
        return jsonify({"error": str(e)}), 500

@app.route('/get-heatmap-data', methods=['GET'])
def get_flights_to_world():
    try:
        flight_data = redis_client.get('flights_data_world')
        if flight_data is None:
            return jsonify({"message": "No flight data available."}), 404
        
        # Convert the string back to a list
        all_flight_data = eval(flight_data)  # Caution: Using eval can be risky. Consider using json.loads() instead.
        
        return jsonify(all_flight_data), 200

    except Exception as e:
        return jsonify({"error": f"Error fetching flight data: {str(e)}"}), 300000
       
@app.route('/all-flights11', methods=['GET'])
def get_flights_to_frankfurt():
    try:
        flight_data = redis_client.get('flights_data')
        if flight_data is None:
            return jsonify({"message": "No flight data available."}), 404
        
        # Convert the string back to a list
        all_flight_data = eval(flight_data)  # Caution: Using eval can be risky. Consider using json.loads() instead.
        
        return jsonify(all_flight_data), 200

    except Exception as e:
        return jsonify({"error": f"Error fetching flight data: {str(e)}"}), 300000

@app.route('/makeprediction', methods=['POST'])
def query():
    try:
        data = request.get_json()
        flight_number = data.get('flightNumber')
        airline_name = data.get('airlineName')

        if not flight_number or not airline_name:
            return jsonify({"message": "Flight number and airline name are required!"}), 400

        # Initialize BigQuery client
        client = bigquery.Client()

        # BigQuery query
        query = f"""
        SELECT
        predicted_is_delayed -- Predicted label (0 or 1)
        FROM
        ML.PREDICT(MODEL `flightmodelfra.fra_arr.flight_delay_model`,
        (
        SELECT
        airline_name,
        flight_number,
        arrival_hour,
        arrival_dayofweek,
        avg_delay
        FROM `flightmodelfra.fra_arr.cleaned_flight_data_with_avg`
        )) WHERE flight_number = {flight_number} AND airline_name = '{airline_name}' LIMIT 1;
        """
        
        # Execute the query
        query_job = client.query(query)
        results = query_job.result()

        # Convert results to JSON
        rows = [dict(row) for row in results]

        if not rows:
            return jsonify({"message": "No data found for the provided flight number and airline name."})

        return jsonify({"message": rows})

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/getFlightData', methods=['GET'])
def get_flight_data():
    try:
        client = bigquery.Client()

        # Get flightNum from the URL parameter
        flight_num = request.args.get('flightNum')
        if not flight_num:
            return jsonify({"error": "Missing flightNum parameter"}), 400

        # Construct the API endpoint URL
        api_url = f"{BASE_URL}{flight_num}?withAircraftImage=false&withLocation=false"

        # Make the API request
        headers = {
            "x-magicapi-key": API_KEY
        }
        response = requests.get(api_url, headers=headers)

        # Check the response status
        if response.status_code == 200:
            # Return the JSON response from the API
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch flight data", "details": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

client = bigquery.Client()


@app.route('/flight-details', methods=['POST'])
def get_flight_details():
    try:
        
        # Get JSON input
        data = request.get_json()
        
        if not data or 'flight_iataNumber' not in data:
            return jsonify({'error': 'Missing flight_iataNumber in request body'}), 400
            
        flight_iata = data['flight_iataNumber'].strip().lower()

        # BigQuery SQL with parameterized query
        query = """
            SELECT
                flight_icaoNumber,
                flight_iataNumber,
                codeshared_airline_iataCode,
                codeshared_flight_number,
                airline_iataCode
            FROM
                 `flightmodelfra.fra_arr.codeshare_real`
            WHERE
                flight_iataNumber = @flight_iata
            LIMIT 1
        """

        # Set up query parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("flight_iata", "STRING", flight_iata),
            ]
        )

        # Execute query
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Process results
        rows = list(results)
        if not rows:
            return jsonify({'error': f'Flight {flight_iata} not found'}), 404

        row = rows[0]
        flight_code = row.flight_iataNumber[:2].lower()
        flight_number = row.flight_iataNumber[2:]

       
        # Configure headless browser
        url = f'https://www.flightstats.com/v2/flight-tracker/{flight_code}/{flight_number}'
        driver = None
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-unsafe-swiftshader")  # Add this flag
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-features=WebGLDraftExtensions")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Navigate to page
        driver.get(url)

        # Wait for critical elements to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='text-helper__TextHelper']"))
        )

        # Find departure times using CSS selector with partial class match
        time_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "div[class*='text-helper__TextHelper']"
        )

        # Extract first two occurrences
        if len(time_elements) >= 2:
            scheduled = time_elements[14].text.strip()
            actual = time_elements[16].text.strip()
            arr_baggage = time_elements[33].text.strip().lower()
            if(actual == "--"): return jsonify({'error': 'Flight not yet departed'}), 500
            if(arr_baggage == "n/a"): return jsonify({'error':'Arrival Gate not yet avialable'}), 500
            print(f"Scheduled Departure: {scheduled}")
            print(f"Actual Departure: {actual}")
        #     return jsonify({
        #     'flight_icaoNumber': row.flight_icaoNumber,
        #     'codeshared_airline_iataCode': row.codeshared_airline_iataCode,
        #     'codeshared_flight_number': row.codeshared_flight_number,
        #     'airline_iataCode': row.airline_iataCode,
        #     'flight_code':flight_code,
        #     'flight_number':flight_number,
        #     'departure_delay':time_difference(actual[:5],scheduled[:5]),
        #     'Scheduled Departure': scheduled[:5],
        #     'Actual Departure': actual[:5]
        # })
            # return jsonify(OrderedDict([
            #     ("type", "arrival"),
            #     ("departure_delay", time_difference(actual[:5],scheduled[:5])),
            #     ("arrival_iataCode", "fra"),
            #     ("arrival_gate", arr_baggage),
            #     ("airline_iataCode", row.airline_iataCode),
            #     ("flight_number", flight_number),
            #     ("codeshared_airline_iataCode", row.codeshared_airline_iataCode),
            #     ("codeshared_flight_number", row.codeshared_flight_number),
            #     ("scheduled_vs_actual_departure", time_difference(actual[:5],scheduled[:5]))
            # ]))
        #     data2 = OrderedDict([
        #     ("type", "arrival"),
        #     ("departure_delay", time_difference(actual[:5], scheduled[:5])),
        #     ("arrival_iataCode", "fra"),
        #     ("arrival_gate", arr_baggage),
        #     ("airline_iataCode", row.airline_iataCode),
        #     ("flight_number", flight_number),
        #     ("codeshared_airline_iataCode", row.codeshared_airline_iataCode),
        #     ("codeshared_flight_number", row.codeshared_flight_number),
        #     ("scheduled_vs_actual_departure", time_difference(actual[:5], scheduled[:5]))
        # ])
            data2 = {
                "scheduled_vs_actual_departure": time_difference(actual[:5], scheduled[:5]),
                "codeshared_flight_number": str(float(row.codeshared_flight_number)),
                "codeshared_airline_iataCode": row.codeshared_airline_iataCode,
                "flight_number": flight_number,
                "airline_iataCode": row.airline_iataCode,
                "arrival_gate": arr_baggage,
                "arrival_iataCode": "fra",
                "departure_delay": time_difference(actual[:5], scheduled[:5]),
                "type": "arrival"
            }
            
             # ✅ Encode categorical inputs
        encoded_data2, error_message = encode_new_input(data2)
        if error_message:
            return jsonify({"error": error_message}), 400

        # ✅ Convert numerical inputs
        numerical_features = ["departure_delay", "scheduled_vs_actual_departure"]
        for col in numerical_features:
            if col in data2:
                try:
                    encoded_data2[col] = float(data2[col])  # Convert to float
                except ValueError:
                    return jsonify({"error": f"❌ Invalid numerical value for '{col}'"}), 400

        # ✅ Ensure all required features are present
        expected_features = ['type', 'departure_delay', 'arrival_iataCode', 'arrival_gate',
                             'airline_iataCode', 'flight_number', 'codeshared_airline_iataCode',
                             'codeshared_flight_number', 'scheduled_vs_actual_departure']

        missing_features = [col for col in expected_features if col not in encoded_data2]
        if missing_features:
            return jsonify({"error": f"❌ Missing features: {missing_features}"}), 400

        # ✅ Convert final data2 into data2Frame with correct feature order
        df = pd.DataFrame([encoded_data2])[expected_features]

        # ✅ Ensure the model has a predict method before calling it
        if not hasattr(model, "predict"):
            return jsonify({"error": "❌ Loaded model does not support prediction. Verify 'best_model.pkl'."}), 500

        # ✅ Make Prediction
        prediction = model.predict(df)

        print("✅ Prediction:", prediction[0])

        return jsonify({"prediction": int(prediction[0])})

        



    except Exception as e:
        return jsonify({'error': f'BigQuery error: {str(e)}'}), 500





@app.route('/all')
def index2():
    return render_template('index55.html')     

@app.route('/temperory')
def index3():
    return render_template('fl-route.html')     

@app.route('/live-route')
def index4():
    return render_template('live-route.html') 

@app.route('/live-route-weather')
def index5():
    return render_template('live-weather.html') 

@app.route('/predict12')
def index6():
    return render_template('historical_data.html') 

@app.route('/live-test')
def index7():
    return render_template('live-route-weather.html') 

@app.route('/live-data')
def index8():
    return render_template('real-time-data.html') 

@app.route('/dashboard')
def index9():
    return render_template('dashboard.html') 

@app.route('/trajectory')
def index10():
    return render_template('trajectory.html') 

@app.route('/predict', methods=['POST'])
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
