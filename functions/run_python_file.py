import os
import subprocess
from google.genai import types


def run_python_file(working_directory, file_path, args=[]):

    try:
        full_path = os.path.join(working_directory, file_path)
        abs_path = os.path.abspath(full_path)
        abs_working = os.path.abspath(working_directory)
        
        if not abs_path.startswith(abs_working):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        
        if not file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'
        
        if not os.path.isfile(abs_path):
            return f'Error: File "{file_path}" not found.'
        
        completed_process = subprocess.run(
            ["python3", abs_path, *args],
            cwd=working_directory,
            capture_output=True,
            timeout=30
        )
        
        stdout = completed_process.stdout.decode()
        stderr = completed_process.stderr.decode()
        
        output_parts = []
        if stdout:
            output_parts.append(f"STDOUT:\n{stdout}")
        if stderr:
            output_parts.append(f"STDERR:\n{stderr}")
        if completed_process.returncode != 0:
            output_parts.append(f"Process exited with code {completed_process.returncode}")
        
        if not output_parts:
            return "No output produced."
        
        return "\n".join(output_parts)   
    except Exception as e:
        return f"Error: executing Python file: {e}"


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file and returns its output (stdout and stderr), constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to execute, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Optional list of command-line arguments to pass to the Python script.",
            ),
        },
        required=["file_path"],
    ),
)
