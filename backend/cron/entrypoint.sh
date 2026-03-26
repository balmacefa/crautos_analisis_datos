#!/bin/bash
set -e

# entrypoint.sh - Docker entrypoint for SMT-Toolbox
# Creates ~/.smt-config.yaml from environment variable and starts gunicorn

echo "🚀 Starting SMT-Toolbox container..."

# Check if SMT_CONFIG environment variable is set
if [ -z "$SMT_CONFIG" ]; then
    echo "⚠️  WARNING: SMT_CONFIG environment variable is not set"
    echo "⚠️  The application may not function correctly without configuration"
else
    echo "📝 Creating ~/.smt-config.yaml from SMT_CONFIG environment variable..."
    
    # Use $HOME explicitly instead of ~ for better compatibility
    CONFIG_FILE="${HOME}/.smt-config.yaml"
    
    # Decode base64-encoded config and create the file
    # The variable should contain base64-encoded YAML content
    echo "$SMT_CONFIG" | base64 -d > "$CONFIG_FILE"
    
    # Check if decoding was successful
    if [ $? -ne 0 ]; then
        echo "⚠️  WARNING: Failed to decode base64 configuration"
        echo "⚠️  Attempting to use raw configuration as fallback..."
        echo "$SMT_CONFIG" > "$CONFIG_FILE"
    fi
    
    # Set proper permissions (owner read/write only)
    chmod 600 "$CONFIG_FILE"
    
    echo "✅ Configuration file created successfully at: $CONFIG_FILE"
    
    # Validate that the file was created and has content
    if [ -s "$CONFIG_FILE" ]; then
        echo "✅ Configuration file size: $(wc -c < "$CONFIG_FILE") bytes"
        # Show first few lines for verification (without sensitive data)
        echo "📄 First 3 lines of config:"
        head -n 3 "$CONFIG_FILE" | sed 's/^/   /'
    else
        echo "⚠️  WARNING: Configuration file is empty"
    fi
fi

# Display startup information
echo "================================================"
echo "SMT-Toolbox DevOps Job Orchestrator"
echo "================================================"
echo "Port: 8081"
echo "User: $(whoami) (UID: $(id -u))"
echo "Working Directory: $(pwd)"
echo "================================================"

# Start gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8081 \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    cron.devops_job_orchestrator:server