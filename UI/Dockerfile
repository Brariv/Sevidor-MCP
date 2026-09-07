# Etapa 1: build de Vite
FROM node:22-alpine AS build
WORKDIR /ui

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Dentro de Docker el widget llama a /api/chat, que nginx reenvía al chatbot.
# Las variables de entorno tienen prioridad sobre el .env de Vite.
ENV VITE_CHAT_API_URL=/api/chat
RUN npm run build

# Etapa 2: servir el build estático con nginx + proxy al chatbot
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /ui/dist /usr/share/nginx/html
EXPOSE 80
