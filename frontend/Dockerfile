# DriveVitals frontend image.
#
# Runs the Vite development server for team development. The live code is
# bind-mounted from the host by docker compose, so editing files on the
# host is reflected in the browser immediately (Vite HMR).

FROM node:22-bookworm-slim

WORKDIR /app/frontend

# Install dependencies before copying code so this layer stays cached while
# application files change. npm ci is deterministic from package-lock.json.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]