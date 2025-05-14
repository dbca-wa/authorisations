# Multistage build to prevent code exposure / reduce image size

# ======================== BUILD IMAGE ========================
# Uses deps and env vars to bake / build the app
# FROM node:23-alpine3.20 as BUILD_IMAGE
# Swap to bun for faster builds
FROM oven/bun:1.2.5-alpine AS build_image

WORKDIR /app
COPY package*.json ./

# Install dependencies, including devDependencies needed for the build process (no --omit=dev)
# RUN npm install
RUN bun add -d esbuild@0.25.2
RUN bun install


# This sets an environment variable named "PATH" to include the "./node_modules/.bin" directory. This ensures that locally installed Node.js modules can be executed directly from the command line without specifying their full path.
ENV PATH="./node_modules/.bin:$PATH"

# This command copies all the files and directories from the current directory (on your host machine, where the Dockerfile is located) into the "/app" directory within the Docker container. from . to . (workdir)
COPY . .

# Set default values for environment variables (This is set on github action for production test and main builds)
ARG VITE_PRODUCTION_BASE_URL=https://127.0.0.1:3000/
ARG VITE_PRODUCTION_BACKEND_API_URL=https://127.0.0.1:8000/v1/api/
ARG VITE_CANNABIS_VERSION=3.0.0

# Set environment variables for runtime access
ENV VITE_PRODUCTION_BASE_URL=$VITE_PRODUCTION_BASE_URL
ENV VITE_PRODUCTION_BACKEND_API_URL=$VITE_PRODUCTION_BACKEND_API_URL
ENV VITE_CANNABIS_VERSION=$VITE_CANNABIS_VERSION

# This command runs the "npm build" script inside the container (it will use above env variables).
# RUN npm run build 
RUN bun run build 

# ======================== PRODUCTION IMAGE ========================
# Uses baked / buiilt app and server w/o large dependencies
# FROM node:22-alpine3.19 as PRODUCTION_IMAGE
FROM oven/bun:1.2.5-slim AS production_image


# Copy built files from the build stage to working dir
WORKDIR /client
COPY --from=build_image /app/dist/ /client/dist/

# Perform operations as root to set ownership and permissions
USER root
RUN mkdir -p /client/node_modules && \
    chown -R bun:bun /client && \
    chmod -R u+rwX /client

# Install serve to serve the built files
# RUN npm install serve -g #FOR NODE
RUN bun add serve

# Switch to the bun user
USER bun

EXPOSE 3000

# Try running serve directly with bun
CMD ["serve", "-s", "dist", "-l", "3000"]