
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install production dependencies for proxy server
RUN npm install express http-proxy-middleware

# Copy built application and proxy server
COPY --from=builder /app/dist ./dist
COPY proxy-server.js ./

EXPOSE 3000

CMD ["node", "proxy-server.js"]
