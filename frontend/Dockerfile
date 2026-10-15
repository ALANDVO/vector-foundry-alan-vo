# Vector Foundry - Frontend Dockerfile
# Multi-stage build for production

# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ .

# Build application
RUN npm run build


# Production stage
FROM nginx:alpine AS production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G appgroup appuser && \
    chown -R appuser:appgroup /var/cache/nginx /var/log/nginx /usr/share/nginx/html

USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]