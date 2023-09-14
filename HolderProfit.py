from requests import get, post
import pandas as pd
import time

# Initialize API key and header
API_KEY = "API KEY HERE"
HEADER = {"x-dune-api-key": API_KEY}

# Base URL
BASE_URL = "https://api.dune.com/api/v1/"

# Function to make API URL
def make_api_url(module, action, ID):
    return f"{BASE_URL}{module}/{ID}/{action}"

# Function to execute a query
def execute_query_with_params(query_id, param_dict):
    """
    Takes in the query ID. And a dictionary containing parameter values.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", query_id)
    response = post(url, headers=HEADER, json={"query_parameters" : param_dict})
    execution_id = response.json()['execution_id']

    return execution_id


# Function to get query status
def get_query_status(execution_id):
    url = make_api_url("execution", "status", execution_id)
    return get(url, headers=HEADER).json()

# Function to get query results
def get_query_results(execution_id):
    url = make_api_url("execution", "results", execution_id)
    return get(url, headers=HEADER).json()

parameters = {
    "chain": "ethereum",
    "decimals": 18,
    "start": 5,
    "token_address": "0x75C97384cA209f915381755c582EC0E2cE88c1BA"
}

# Execute the query
query_id = "3024597"  # Replace with your actual query ID
execution_id = execute_query_with_params(query_id, parameters)  # Added parameters here

# Check the query status until it's completed
while True:
    status_response = get_query_status(execution_id)
    if status_response['state'] == 'QUERY_STATE_COMPLETED':
        break
    time.sleep(5)  # Wait for 5 seconds before checking again

# Get the query results
result_response = get_query_results(execution_id)

# Check if 'result' key exists in the response
if 'result' in result_response:
    data = pd.DataFrame(result_response['result']['rows'])
    data.to_csv("sample_data.csv")
else:
    print("Key 'result' not found. Full response:", result_response)