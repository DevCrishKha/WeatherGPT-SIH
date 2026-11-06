import requests
from dotenv import load_dotenv, set_key, find_dotenv
import os

load_dotenv()

url = "https://api.imd.gov.in/api/oauth/token.php"

payload = {
  "email": os.getenv("EMAIL"),
  "password": os.getenv("PASSWD")
}

headers = {
    "Content-Type":"application/json"
}

def get_JWT() -> None:
  response = requests.post(url, json=payload, headers=headers)
  
  JWT_TOKEN = response.json()['access_token']

  print(response.status_code)
  print(response.text)
  print("JWT_TOKEN:",JWT_TOKEN)
  
  # 1. Locate and load the .env file
  dotenv_path = find_dotenv()
  set_key(dotenv_path, "JWT_Token", JWT_TOKEN, quote_mode="never")

get_JWT()
