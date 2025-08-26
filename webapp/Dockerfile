# syntax=docker/dockerfile:1
FROM node:20-slim

WORKDIR /app

COPY webapp/package.json webapp/package-lock.json* webapp/pnpm-lock.yaml* ./
RUN if [ -f package-lock.json ]; then npm ci; elif [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i --frozen-lockfile; else npm i; fi

COPY webapp/ .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
