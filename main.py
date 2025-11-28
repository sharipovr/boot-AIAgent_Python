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
if len(sys.argv) < 2:
    print("No content provided ,exiting program")
    sys.exit(1)

isVerbose = True if sys.argv[-1] == "--verbose" else False

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model = "gemini-2.0-flash-001"
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

while True:
    res = client.models.generate_content(
        model=model,
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        ),
    )

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
        messages.append(types.Content(role="tool", parts=function_call_results))
    else:
        # No more function calls, print final response and exit loop
        print(res.text)
        break

if isVerbose:
    print("User prompt:", content)
    print("Prompt tokens:", res.usage_metadata.prompt_token_count)
    print("Response tokens:", res.usage_metadata.candidates_token_count)

