#!/bin/sh

# Generate runtime config file with environment variables
cat > /usr/share/nginx/html/config.js << EOF
window.__RUNTIME_CONFIG__ = {
  keycloakUrl: '${VITE_KEYCLOAK_URL:-}',
  keycloakRealm: '${VITE_KEYCLOAK_REALM:-}',
  keycloakClientId: '${VITE_KEYCLOAK_CLIENT_ID:-}'
};
EOF

# Start nginx
exec nginx -g "daemon off;"