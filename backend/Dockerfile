FROM node:20-slim

# better-sqlite3 needs a build toolchain for its native bindings
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY . .

ENV NODE_ENV=production
EXPOSE 4000

CMD ["node", "server.js"]
