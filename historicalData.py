import requests
from requests.auth import HTTPBasicAuth

url = "https://trino.opensky-network.org/"
username = "Khan.Rehaan.srh-hochschule@outlook.com"
password = "supermanLol796#1"

# Send a SQL query via POST
query = {"query": "SHOW TABLES"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=query, auth=HTTPBasicAuth(username, password), headers=headers)
if response.status_code == 200:
    print("Query successful!")
    print(response.json())
else:
    print(f"Failed with status code: {response.status_code}")
    print(response.text)
