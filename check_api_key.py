import requests
import json
import os

# Load API key from environment variables for security
API_KEY = os.getenv("VITE_OPENROUTER_API_KEY") 
if not API_KEY:
    raise ValueError("API key not found. Set the VITE_OPENROUTER_API_KEY environment variable.")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000", # Placeholder - Replace if needed
    "X-Title": "API Key Check Script", # Placeholder - Replace if needed
}

# Using a simple text-based model and prompt for the check
data = json.dumps({
    "model": "openai/gpt-3.5-turbo", # Using a common and relatively cheap model
    "messages": [
        {
            "role": "user",
            "content": "Say 'test successful' if you are working."
        }
    ],
    "max_tokens": 10 # Limit response length
})

try:
    response = requests.post(API_URL, headers=headers, data=data, timeout=30) # Added timeout
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    # Pretty print the JSON response
    print(json.dumps(response.json(), indent=2))

    # You can add more specific checks here, e.g., check content of the response
    if "test successful" in response.json().get('choices', [{}])[0].get('message', {}).get('content', '').lower():
        print("API Key seems to be working correctly!")
    else:
        print("API Key might be working, but the expected response content was not found.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
            print("Could not read response body.")

except Exception as e:
    print(f"An unexpected error occurred: {e}") 
