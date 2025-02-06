# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /admin

# Copy package.json first
COPY package.json ./

# Install dependencies and generate yarn.lock
RUN yarn install