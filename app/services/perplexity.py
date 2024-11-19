from openai import OpenAI
import os
# import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PERPLEXITY_API_KEY")

# Set your API key as an environment variable for security
# os.environ["PERPLEXITY_API_KEY"] = "your_api_key_here"

# Initialize the OpenAI client with Perplexity's base URL
client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

def search_ucr_rates(input_text):
    messages = [
        {
            "role": "system",
            "content": "You are a skilled AI researcher that provides information about UCR rates for medical procedures in the United States of America."
        },
        {
            "role": "user",
            "content": f'''What are the standardized UCR rates for the procedure (or medical code) in {input_text}   
            Search online and find as many sources available within the correct (same) city / state as the patient
            and calculate the average. Use this as your reference point. Provide an output with only one sentence.
            It should state the standardized UCR rate (the average) for the medical procedure in the city/state the user underwent it.
            Make it clear that this is to be labelled and used as 'ucr_rate'.
            '''
        }
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=messages,
        )
        # sys.stderr(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"


# result = search_ucr_rates(bill)
# print(result)

# Main function
# def main():
#     # Run the analysis with the provided medical bill
#     #use below code once RAG comes in
#     # filepath = sys.argv[1]
#     # with open(filepath, 'r') as file:
#     #     bill = json.load(file)
#     final_report = search_ucr_rates("thre isnt much to say")
#     print(final_report)

# Entry point for the script
# if __name__ == "__main__":
#     main()