# Stage 1: Build the React application
FROM node:20-slim AS build-stage

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:stable-alpine

# Copy the build output to Nginx's html directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx config
RUN echo 'server {\
    listen 80;\
    server_name localhost;\
    location / {\
        root /usr/share/nginx/html;\
        index index.html index.htm;\
        try_files $uri $uri/ /index.html;\
    }\
    location /api {\
        proxy_pass http://backend:8000;\
        proxy_set_header Host $http_host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
