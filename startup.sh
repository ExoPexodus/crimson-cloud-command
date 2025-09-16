#!/bin/sh

# Replace environment variable placeholders in built files
if [ -n "$VITE_API_URL" ]; then
  echo "Injecting VITE_API_URL: $VITE_API_URL"
  find /usr/share/nginx/html -name "*.js" -exec sed -i "s|__VITE_API_URL__|$VITE_API_URL|g" {} \;
else
  echo "VITE_API_URL not set, using fallback logic"
  find /usr/share/nginx/html -name "*.js" -exec sed -i "s|'__VITE_API_URL__'||g" {} \;
fi

# Start nginx
exec nginx -g "daemon off;"