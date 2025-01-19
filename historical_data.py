from google.cloud import bigquery

def query_bigquery(query):
    # Initialize BigQuery client
    client = bigquery.Client()

    # Perform the query
    query_job = client.query(query)

    # Wait for the query to complete and fetch results
    results = query_job.result()

    # Display the results
    for row in results:
        print(dict(row))  # Convert each row to a dictionary for easy readability

# Example SQL query
sql_query = """
SELECT
 *,
 predicted_is_delayed, -- Predicted label (0 or 1)
 predicted_is_delayed_probs -- Probability of delay
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
 )) WHERE flight_number = 1775 AND airline_name = 'kenya airways' LIMIT 1;
"""

if __name__ == "__main__":
    query_bigquery(sql_query)
