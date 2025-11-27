import os

def get_files_info(working_directory, directory="."):
    try:
        full_path = os.path.join(working_directory, directory)
        abs_path = os.path.abspath(full_path)
        abs_working = os.path.abspath(working_directory)
        
        if not abs_path.startswith(abs_working):
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        
        if not os.path.isdir(abs_path):
            return f'Error: "{directory}" is not a directory'
        
        result = []
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            file_size = os.path.getsize(item_path)
            is_dir = os.path.isdir(item_path)
            result.append(f"- {item}: file_size={file_size} bytes, is_dir={is_dir}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error: {e}"