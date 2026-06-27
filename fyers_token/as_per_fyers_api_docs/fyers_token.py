# https://myapi.fyers.in/docsv3#tag/Authentication-and-Login-Flow-User-Apps
# Import the required module from the fyers_apiv3 package
from fyers_apiv3 import fyersModel
#------------------------------------
import os
from pathlib import Path
from dotenv import load_dotenv

# Moves up levels relative to this specific script file
# Example: If script is in root/src/main.py -> .parent.parent is project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
print("PROJECT_ROOT =", PROJECT_ROOT)
root_env = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=root_env)
#------------------------------------

# Replace these values with your actual API credentials
client_id = os.getenv("BROKER_API_KEY") #its BROKER_API_KEY in .env file
secret_key = os.getenv("BROKER_API_SECRET")   # its BROKER_API_SECRET in .env file
redirect_uri = os.getenv("REDIRECT_URL", "http://127.0.0.1:5000/fyers/callback") # its REDIRECT_URL in .env file
response_type = "code"  
state = "sample_state"
grant_type = "authorization_code" 

# Create a session model with the provided credentials
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type
)

# Generate the auth code using the session model
response = session.generate_authcode()

# Print the auth code received in the response
print(response)

 
# Make changes here ... Ask user to paste it
# The authorization code received from Fyers after the user grants access
auth_code = input("Please paste the authorization code received from Fyers: ")

# Create a session object to handle the Fyers API authentication and token generation
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key, 
    redirect_uri=redirect_uri, 
    response_type=response_type, 
    grant_type=grant_type
)

# Set the authorization code in the session object
session.set_token(auth_code)

# Generate the access token using the authorization code
response = session.generate_token()

# Print the response, which should contain the access token and other details
print(response)