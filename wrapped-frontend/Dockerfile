# syntax=docker/dockerfile:1
# Use Node.js for building
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (for better caching)
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy the rest of the application
COPY . .

# Build the Next.js app
# Cache Next.js' own incremental build cache across builds (webpack/SWC cache)
RUN --mount=type=cache,target=/app/.next/cache npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/jsconfig.json ./jsconfig.json

EXPOSE 3000

# Start the application
CMD ["npm", "start"]
