import subprocess
import os
import tempfile

def run_python_code(code: str) -> str:
    """
    Writes python code to a temporary file, executes it safely with a timeout, 
    and returns its standard output and errors combined.
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name
            
        # Run the script with a 10-second timeout to prevent infinite loops
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout
        # We also capture STDERR specifically since bug reproductions often throw stack traces
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
            
        # Return whatever was printed or errored
        return output.strip() if output.strip() else "Process exited successfully without any output."
        
    except subprocess.TimeoutExpired:
        return "Execution Error: Script timed out after 10 seconds. Check for infinite loops."
    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        # Cleanup the temp script
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
