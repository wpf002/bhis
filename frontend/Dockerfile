# Build the static SPA, then serve it with nginx (which also proxies /api to the
# backend so the app's relative /api/v1 calls work in production without CORS).
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
# nginx:alpine runs envsubst over /etc/nginx/templates/*.template at start, but
# only substitutes variables present in the environment — so $host etc. are safe.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV BACKEND_URL=http://backend:8000
EXPOSE 80
