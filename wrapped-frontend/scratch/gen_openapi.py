import json
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from backend.api.main import app

# Generate OpenAPI JSON
openapi_schema = app.openapi()

with open('openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print("openapi.json generated successfully")
