FROM node:18-alpine

WORKDIR /app

# Install dependencies first (for better caching)
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Development environment
ENV NODE_ENV=development

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with host=0.0.0.0 to allow external connections
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]