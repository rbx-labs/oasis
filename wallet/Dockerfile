# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /wallet

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt