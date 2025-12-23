import os
from dotenv import load_dotenv
from google import genai
import sys
from google.genai import types
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.run_python_file import schema_run_python_file, run_python_file
from functions.write_file import schema_write_file, write_file

working_directory = "./calculator"

function_map = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}


def call_function(function_call_part, verbose=False):
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")
    
    function_name = function_call_part.name
    func = function_map.get(function_name)
    if func is None:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )
    
    args = dict(function_call_part.args)
    args["working_directory"] = working_directory
    
    function_result = func(**args)
    
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )


load_dotenv()

isVerbose = "--verbose" in sys.argv

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model = "gemini-2.5-flash"
# Use default prompt if no argument provided
if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == "--verbose"):
    content = "Why is Boot.dev such a great place to learn backend development? Use one paragraph maximum."
else:
    content = sys.argv[1]
system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)

messages = [
    types.Content(role="user", parts=[types.Part(text=content)]),
]

for _ in range(20):
    try:
        res = client.models.generate_content(
            model=model,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions], system_instruction=system_prompt
            ),
        )

        # Verify usage_metadata is not None
        if res.usage_metadata is None:
            raise RuntimeError("usage_metadata is None, indicating a failed API request")

        # Check if model is finished (no function calls and has text response)
        if not res.function_calls and res.text:
            print(f"User prompt: {content}")
            print(f"Prompt tokens: {res.usage_metadata.prompt_token_count}")
            print(f"Response tokens: {res.usage_metadata.candidates_token_count}")
            print("Response:")
            print(res.text)
            break

        # Process function calls
        if res.function_calls:
            # Add the model's response (with function calls) to messages
            for candidate in res.candidates:
                messages.append(candidate.content)
            
            # Execute each function call and collect results
            function_call_results = []
            for function_call_part in res.function_calls:
                function_call_result = call_function(function_call_part, verbose=isVerbose)
                if not function_call_result.parts[0].function_response.response:
                    raise Exception("Function call result does not have a response")
                function_call_results.append(function_call_result.parts[0])
                if isVerbose:
                    print(f"-> {function_call_result.parts[0].function_response.response}")
            
            # Add all tool results to messages
            messages.append(types.Content(role="user", parts=function_call_results))
    except Exception as e:
        print(f"Error: {e}")
        break
else:
    print("Max iterations reached. Exiting.")
