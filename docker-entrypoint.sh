#!/bin/sh

# Generate runtime configuration file
cat > /usr/share/nginx/html/config.js << EOF
window.RUNTIME_CONFIG = {
  KEYCLOAK_URL: '${VITE_KEYCLOAK_URL:-}',
  KEYCLOAK_REALM: '${VITE_KEYCLOAK_REALM:-}',
  KEYCLOAK_CLIENT_ID: '${VITE_KEYCLOAK_CLIENT_ID:-}',
  API_BASE_URL: '${VITE_API_BASE_URL:-}'
};
EOF

echo "Generated runtime configuration:"
cat /usr/share/nginx/html/config.js

# Process nginx template with environment variable substitution
echo "Processing nginx configuration template..."
envsubst '${VITE_API_BASE_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Generated nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'
