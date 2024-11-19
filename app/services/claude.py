from anthropic import Client
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')

if api_key is None:
    print("Error: ANTHROPIC_API_KEY is not set.")
else:
    # Initialize the client with your API key
    client = Client(api_key=api_key)

def analyze_with_claude(input_text):
    """
    Analyze the input text using Claude AI and return the response.
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": f'''

                    {input_text}
                '''
            }
        ]
    )
    # Extract response content from the Claude API
    response_content = message.content[0].text
    return response_content

def save_response_to_file(response_data, filename='claude-response.json'):
    """
    Save the Claude AI response to a JSON file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")
