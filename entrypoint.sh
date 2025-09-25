#!/bin/sh

# Function to substitute environment variables in config.js
substitute_env_vars() {
    # Create config.js with actual environment variables
    envsubst < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js
}

# Copy config.js as template if it doesn't exist
if [ ! -f /usr/share/nginx/html/config.js.template ]; then
    cp /usr/share/nginx/html/config.js /usr/share/nginx/html/config.js.template
fi

# Substitute environment variables
substitute_env_vars

# Start nginx
exec "$@"