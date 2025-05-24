import json
import sys
import os

# Assuming the script is run from the root of the repository,
# add the 'app' directory to the Python path to allow importing 'main'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

try:
    from main import app # Assuming your FastAPI app instance is named 'app' in 'main.py'
except ImportError as e:
    print(f"Error importing FastAPI app: {e}", file=sys.stderr)
    print(f"Current sys.path: {sys.path}", file=sys.stderr)
    # Attempt to list contents of 'app' directory to help debug
    try:
        print(f"Contents of 'app' directory: {os.listdir('app')}", file=sys.stderr)
    except FileNotFoundError:
        print("'app' directory not found at current location.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    try:
        openapi_schema = app.openapi()
        print(json.dumps(openapi_schema, indent=2))
    except Exception as e:
        print(f"Error generating OpenAPI schema: {e}", file=sys.stderr)
        sys.exit(1)
