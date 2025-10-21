# Development Dockerfile for React with hot-reload
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

EXPOSE 3003

# Run in development mode with hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]