from flask import Flask, jsonify, request, render_template
import requests
import redis
import threading
import time
from google.cloud import bigquery
from dotenv import load_dotenv
import os

app = Flask(__name__)

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

# Endpoint to handle flight query
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

@app.route('/predict')
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


if __name__ == '__main__':
    app.run(debug=True)
