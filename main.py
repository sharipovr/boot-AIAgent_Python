import os
from dotenv import load_dotenv
from google import genai
import sys
from google.genai import types


load_dotenv()
if len(sys.argv) < 2:
    print("No content provided ,exiting program")
    sys.exit(1)

isVerbose = True if sys.argv[-1] == "--verbose" else False

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model = "gemini-2.0-flash-001"
content = sys.argv[1]

messages = [
    types.Content(role="user", parts=[types.Part(text=content)]),
]

res = client.models.generate_content(model=model, contents=messages)   

print(res.text)

if isVerbose:
    print("User prompt:", content)
    print("Prompt tokens:", res.usage_metadata.prompt_token_count)
    print("Response tokens:", res.usage_metadata.candidates_token_count)

