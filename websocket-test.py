from flask import Flask, jsonify, render_template
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

EUROPE_AREA = {
    "lamin": 47.27,  # Minimum latitude
    "lomin": 5.87,   # Minimum longitude
    "lamax": 55.06,  # Maximum latitude
    "lomax": 15.04   # Maximum longitude
}

@app.route('/all-flights', methods=['GET'])
def get_flights_to_frankfurt():
    try:

        # Set up the authentication credentials
        username = 'level9nine'
        password = 'supermanLol796#1'

        # Fetch flights from the OpenSky API with authentication
        response = requests.get('https://opensky-network.org/api/states/all', params={
            'lamin': EUROPE_AREA['lamin'],
            'lomin': EUROPE_AREA['lomin'],
            'lamax': EUROPE_AREA['lamax'],
            'lomax': EUROPE_AREA['lomax']
        }, auth=(username, password))  # Adding basic auth
        
        response.raise_for_status()  # Raise an error for bad responses
        flights = response.json().get('states', [])

        if not flights:
            return jsonify({"message": "No flights en route to Frankfurt found."}), 404

        all_flight_data = []  # List to store each flight's data

        for flight in flights:
            # Unpack the relevant flight data
            icao24 = flight[0]
            destination = flight[2]
            callsign = flight[1].strip() if flight[1] else None
            longitude = flight[5]
            latitude = flight[6]
            velocity = flight[9] if len(flight) > 9 else None
            heading = flight[10] if len(flight) > 10 else None

            # Create a dictionary for the flight data
            flight_data = {
                "Flight": callsign,
                "ICAO24": icao24,
                "Destination": destination,
                "latitude": latitude,
                "longitude": longitude,
                "Speed": f"{velocity} m/s" if velocity is not None else None,
                "Heading": f"{heading}°" if heading is not None else None
            }

            # Append each flight's data to the list
            all_flight_data.append(flight_data)

        # Return all flight data as a single JSON array
        return jsonify(all_flight_data), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching flights: {str(e)}"}), 500


@app.route('/all')
def index():
    return render_template('index55.html')  # Ensure your HTML file is named index.html

if __name__ == '__main__':
    app.run(debug=True)
