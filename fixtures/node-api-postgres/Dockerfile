# syntax=docker/dockerfile:1

FROM node:24-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:24-alpine AS development
WORKDIR /app
ENV NODE_ENV=development
COPY --from=dependencies --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node package.json package-lock.json ./
COPY --chown=node:node app ./app
COPY --chown=node:node migrations ./migrations
USER node
CMD ["npm", "run", "dev"]

FROM gcr.io/distroless/nodejs24-debian13:nonroot AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000
COPY --from=dependencies --chown=nonroot:nonroot /app/node_modules ./node_modules
COPY --chown=nonroot:nonroot package.json package-lock.json ./
COPY --chown=nonroot:nonroot app ./app
COPY --chown=nonroot:nonroot migrations ./migrations
USER nonroot
EXPOSE 3000
CMD ["app/server.js"]
