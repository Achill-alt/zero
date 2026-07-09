# ── Stage 1: Build ──────────────────────────────────────────────────
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies (layer cached unless package*.json changes)
COPY package*.json .
RUN npm ci --silent

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Serve (nginx) ──────────────────────────────────────────
FROM nginx:alpine

# Replace default nginx config with SPA + API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
