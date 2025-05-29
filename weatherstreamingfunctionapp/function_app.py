import logging
import requests
import json
import os  # For environment variables if you choose to use them for some configs

import azure.functions as func
from azure.eventhub import EventHubProducerClient, EventData
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# --- Module-Level Configurations ---
# Consider fetching some of these from Application Settings/Environment Variables
# For example: os.environ.get("KEY_VAULT_URL")
KEY_VAULT_URL = "https://keyvault-weatherstream.vault.azure.net/"
WEATHER_API_KEY_SECRET_NAME = "weatherapikey"

# Event Hub Configuration
EVENT_HUB_FULLY_QUALIFIED_NAMESPACE = "weather-evenhub-namespace.servicebus.windows.net" # Make sure this is your EH Namespace FQDN
EVENT_HUB_NAME = "weatherstreamingeventhub"

# Weather API Configuration
WEATHER_API_BASE_URL = "http://api.weatherapi.com/v1/"
WEATHER_API_LOCATION = "Bengaluru" # Or make this configurable
WEATHER_API_FORECAST_DAYS = 3

# --- Initialize Azure Clients (once per Function App instance) ---
# Using Managed Identity of Function App for Azure services
try:
    AZURE_CREDENTIAL = DefaultAzureCredential()
    SECRET_CLIENT = SecretClient(vault_url=KEY_VAULT_URL, credential=AZURE_CREDENTIAL)
    
    # Get API key at startup
    WEATHER_API_KEY = SECRET_CLIENT.get_secret(WEATHER_API_KEY_SECRET_NAME).value

    EVENT_HUB_PRODUCER_CLIENT = EventHubProducerClient(
        fully_qualified_namespace=EVENT_HUB_FULLY_QUALIFIED_NAMESPACE,
        eventhub_name=EVENT_HUB_NAME,
        credential=AZURE_CREDENTIAL
    )
except Exception as e:
    # Log critical failure if clients or initial secrets can't be loaded
    logging.critical(f"CRITICAL: Failed to initialize Azure clients or load initial secrets: {e}")
    # Setting to None so function can check and avoid running, or fail explicitly later
    AZURE_CREDENTIAL = None
    SECRET_CLIENT = None
    WEATHER_API_KEY = None
    EVENT_HUB_PRODUCER_CLIENT = None

# --- Main Azure Function Definition ---
app = func.FunctionApp()

@app.timer_trigger(schedule="*/60 * * * * *",  # Runs "at second 0 of every minute"
                   arg_name="myTimer", 
                   run_on_startup=False,
                   use_monitor=False) 
def weatherapifunction(myTimer: func.TimerRequest) -> None:
    if not all([AZURE_CREDENTIAL, SECRET_CLIENT, WEATHER_API_KEY, EVENT_HUB_PRODUCER_CLIENT]):
        logging.error("One or more Azure clients or the API key were not initialized. Aborting execution.")
        return

    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function weatherapifunction started.')
    
    _fetch_process_and_send_weather_data()

# --- Helper Functions (Module Level) ---

def _get_weather_api_data(endpoint_url: str, params: dict):
    """Generic function to call the weather API and handle responses."""
    try:
        response = requests.get(endpoint_url, params=params, timeout=15) # Added timeout
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # response.text might contain more details from the API provider
        logging.error(f"HTTP error occurred for {endpoint_url}: {http_err} - {response.text if 'response' in locals() else 'No response text'}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request exception occurred for {endpoint_url}: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred calling {endpoint_url}: {e}")
    return None # Return None to indicate failure

def _get_current_weather(base_url, api_key, location):
    current_weather_url = f"{base_url}/current.json"
    params = {'key': api_key, 'q': location, "aqi": 'yes'}
    return _get_weather_api_data(current_weather_url, params)

def _get_forecast_weather(base_url, api_key, location, days):
    forecast_url = f"{base_url}/forecast.json"
    params = {"key": api_key, "q": location, "days": days}
    return _get_weather_api_data(forecast_url, params)

def _get_alerts(base_url, api_key, location):
    alerts_url = f"{base_url}/alerts.json"
    params = {'key': api_key, 'q': location, "alerts": 'yes'}
    return _get_weather_api_data(alerts_url, params)

def _flatten_data(current_weather, forecast_weather, alerts):
    # (Your existing flatten_data logic is good, assuming input dicts are valid)
    # Add checks for None if any component could be optional even on success
    location_data = current_weather.get("location", {})
    current = current_weather.get("current", {})
    condition = current.get("condition", {})
    air_quality = current.get("air_quality", {})
    forecast = forecast_weather.get("forecast", {}).get("forecastday", [])
    alert_list = alerts.get("alerts", {}).get("alert", [])

    return {
        'name': location_data.get('name'),
        'region': location_data.get('region'),
        'country': location_data.get('country'),
        'lat': location_data.get('lat'),
        'lon': location_data.get('lon'),
        'localtime': location_data.get('localtime'),
        'temp_c': current.get('temp_c'),
        'is_day': current.get('is_day'),
        'condition_text': condition.get('text'),
        'condition_icon': condition.get('icon'),
        'wind_kph': current.get('wind_kph'),
        'wind_degree': current.get('wind_degree'),
        'wind_dir': current.get('wind_dir'),
        'pressure_in': current.get('pressure_in'),
        'precip_in': current.get('precip_in'),
        'humidity': current.get('humidity'),
        'cloud': current.get('cloud'),
        'feelslike_c': current.get('feelslike_c'),
        'uv': current.get('uv'),
        'air_quality': {
            'co': air_quality.get('co'),
            'no2': air_quality.get('no2'),
            'o3': air_quality.get('o3'),
            'so2': air_quality.get('so2'),
            'pm2_5': air_quality.get('pm2_5'),
            'pm10': air_quality.get('pm10'),
            'us-epa-index': air_quality.get('us-epa-index'),
            'gb-defra-index': air_quality.get('gb-defra-index')
        },
        'alerts': [
            {'headline': alert.get('headline'), 'severity': alert.get('severity'), 
             'description': alert.get('desc'), 'instruction': alert.get('instruction')}
            for alert in alert_list
        ],
        'forecast': [
            {'date': day.get('date'), 'maxtemp_c': day.get('day', {}).get('maxtemp_c'),
             'mintemp_c': day.get('day', {}).get('mintemp_c'), 
             'condition': day.get('day', {}).get('condition', {}).get('text')}
            for day in forecast
        ]
    }

def _send_event_to_hub(event_data_dict):
    if EVENT_HUB_PRODUCER_CLIENT is None:
        logging.error("Event Hub producer client is not initialized. Cannot send event.")
        return False
    try:
        event_data_batch = EVENT_HUB_PRODUCER_CLIENT.create_batch()
        event_data_batch.add(EventData(json.dumps(event_data_dict)))
        EVENT_HUB_PRODUCER_CLIENT.send_batch(event_data_batch)
        logging.info(f"Successfully sent data for location {event_data_dict.get('name', 'N/A')} to Event Hub.")
        return True
    except Exception as e:
        logging.error(f"Error sending data to Event Hub: {e}")
        return False

def _fetch_process_and_send_weather_data():
    logging.info("Fetching weather data...")

    # Get data from API
    # WEATHER_API_KEY is now a global variable loaded at startup
    current_weather = _get_current_weather(WEATHER_API_BASE_URL, WEATHER_API_KEY, WEATHER_API_LOCATION)
    forecast_weather = _get_forecast_weather(WEATHER_API_BASE_URL, WEATHER_API_KEY, WEATHER_API_LOCATION, WEATHER_API_FORECAST_DAYS)
    alerts = _get_alerts(WEATHER_API_BASE_URL, WEATHER_API_KEY, WEATHER_API_LOCATION)

    # Check if all essential data was successfully fetched
    if not current_weather or not forecast_weather or not alerts:
        logging.error("Failed to retrieve one or more essential weather data components. Aborting for this run.")
        return

    # Flatten and merge data
    logging.info("Flattening and merging data...")
    merged_data = _flatten_data(current_weather, forecast_weather, alerts)
    
    # Sending the weather data to Event Hub
    logging.info("Sending data to Event Hub...")
    _send_event_to_hub(merged_data)
    
    logging.info("Weather data processing complete for this run.")

# To close the producer client when the function app is shutting down (optional but good practice)
# This is harder to achieve reliably in Azure Functions serverless model without __del__ or atexit complexities.
# For EventHubProducerClient, it's often acceptable to let the host manage closure, 
# or re-create if an issue is suspected after long runs.
# However, if you scale out, many instances will have their own clients.
# def close_clients():
#    if EVENT_HUB_PRODUCER_CLIENT:
#        EVENT_HUB_PRODUCER_CLIENT.close()
# atexit.register(close_clients) # atexit can be unreliable in some serverless environments.