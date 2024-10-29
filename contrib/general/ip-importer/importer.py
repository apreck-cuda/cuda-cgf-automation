import requests
import json
import logging

# Define variables 
API_KEY = "0sRYlI0PHb0L7t8UJDd4xPKBMSbHuZiB" #API Key for CC
JSON_URL = "http://localhost:8123/random_ips.json" #URL to access your json list including the ip 
CC_IP = "10.10.10.110:8080" #CC IP including API port.
JSON_ID = "ips" #Identifier for the IPs array within JSON
RANGE = ""  #OPTIONAL Range for Global Range objects. Leave empty if global object should be used.
CLUSTER = ""  #OPTIONAL Cluster for Global Cluster objects. Leave empty if range object should be used.
BOX = ""  #OPTIONAL Box name for Box objects. Leave empty if cluster object should be used.
FW_SERVICE_NAME = "" # Only for box level Objects.
NAME = "ImportedObject1"  #If not set - will be created as ImportedromURL by default.

# Set default endpoint to global
API_ENDPOINT = f"http://{CC_IP}/rest/cc/v1/config/global/firewall/objects/networks"

# Adjust endpoint based on RANGE, CLUSTER, and BOX values
if RANGE:
    API_ENDPOINT = f"http://{CC_IP}/rest/cc/v1/config/ranges/{RANGE}/firewall/objects/networks"
    if CLUSTER:
        API_ENDPOINT = f"http://{CC_IP}/rest/cc/v1/config/ranges/{RANGE}/clusters/{CLUSTER}/firewall/objects/networks"
        if BOX:
            API_ENDPOINT = f"http://{CC_IP}/rest/cc/v1/config/ranges/{RANGE}/clusters/{CLUSTER}/boxes/{BOX}/service-container/{FW_SERVICE_NAME}/firewall/objects/networks"

# API headers for CC
HEADERS = {
    "Content-Type": "application/json",
    "X-API-TOKEN": API_KEY
}

# Logging
logging.basicConfig(
    filename='firewall_import.log',  # Log file name
    level=logging.INFO,              # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S'      # Date format
)

# Function to download the JSON from a URL
def download_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Successfully downloaded JSON from {url}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error downloading JSON from {url}: {e}")
        return None

# Function to import IP into the firewall object
def import_ip_to_firewall(ips, API_ENDPOINT, object_name):
    included_entries = [{"entry": {"ip": ip}} for ip in ips]  # Create the list of IP entries

    # Create request body
    body = {
        "color": "#ff0000", # use red ti visulise the network object
        "comment": "This is an object imported from the URL by ip-porter script.",
        "included": included_entries,
        "name": object_name,
        "type": "generic"
    }

    # Check if the object already exists
    try:
        response = requests.get(f"{API_ENDPOINT}/{object_name}", headers=HEADERS)
        if response.status_code == 200:
            logging.info(f"Object '{object_name}' already exists. Patching with new entries.")
            # Object exists, patch it
            patch_body = {"included": included_entries}
            response = requests.put(f"{API_ENDPOINT}/{object_name}", headers=HEADERS, json=patch_body)
            response.raise_for_status()
            logging.info(f"Successfully updated object '{object_name}' with new IPs.")
        elif response.status_code == 404:
            logging.info(f"Object '{object_name}' not found. Creating new object.")
            # Object does not exist, create it
            response = requests.post(API_ENDPOINT, headers=HEADERS, json=body)
            response.raise_for_status()  # Raise an exception for HTTP errors
            logging.info(f"Successfully created and imported IPs to the new object '{object_name}'.")
        elif response.status_code == 403:
                logging.info(f"Aithorization failed please verify your API toklen and permissions.")
        else:
            logging.error(f"Unexpected error checking object '{object_name}': {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error handling object '{object_name}': {e}")

# Main function to handle the process
def main():
    json_data = download_json(JSON_URL)
    logging.info(f"Using API Endpoint {API_ENDPOINT}")

    if json_data and JSON_ID in json_data:
        ips = json_data[JSON_ID]
        logging.info(f"Found {len(ips)} IPs in the '{JSON_ID}' array.")

        object_name = NAME if NAME else "ImportedFromURL"
        import_ip_to_firewall(ips, API_ENDPOINT, object_name)
    else:
        logging.error("No '{JSON_ID}' array found in the downloaded JSON.")

if __name__ == "__main__":
    main()
