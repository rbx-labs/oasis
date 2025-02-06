# Oasis API Server

## Overview

Oasis is an audio processing and transcription service that provides speaker diarization and transcription capabilities.

## Features

- Audio file upload and management
- Speech-to-text transcription
- Speaker diarization using Gladia API
- Scheduled tasks management
- API key authentication

## Prerequisites

- Docker and docker-compose

## Installation

### Using Docker Compose

1. Clone the repository:

```bash
git clone https://github.com/rbx-labs/oasis.git
cd oasis
```

2. Create .env file:

```bash
cp .env.example .env
# Edit .env file with your settings
```

3. Build and run with docker-compose:

```bash
docker-compose up --build
```

4. Run in detached mode:

```bash
docker-compose up -d
```

5. Stop the containers:

```bash
docker-compose down
```

## Ngrok Setup

Ngrok is used to expose the FastAPI server to the internet. To use Ngrok, you need to set up an authentication token.

1. Sign up for an Ngrok account and get your authentication token.

2. Add the token to your `.env` file:

```env
NGROK_AUTHTOKEN=your-ngrok-auth-token
```

3. When you run the application using Docker Compose, Ngrok will automatically create a public URL for your FastAPI server.

4. Access the Ngrok web interface to see the generated URL:

```bash
http://localhost:4040
```

## API Documentation

Once the application is running, you can access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`

  - Interactive API testing interface
  - Detailed request/response examples
  - Try out API endpoints directly in the browser

- ReDoc: `http://localhost:8000/redoc`
  - Clean and organized documentation
  - Detailed schema information
  - Easy-to-read format

For detailed usage instructions, parameter descriptions, and example requests/responses, please refer to these documentation interfaces.

## Authentication

The API uses API Key authentication. Include the API key in your requests:

```bash
# Example: Get latest audio file
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/audio/latest
```

All requests must include the `X-API-Key` header with a valid API key. The API key should be set in your `.env` file:

```env
API_KEY=your-super-secret-api-key
```

## Environment Variables

| Variable            | Description                           | Default               |
| ------------------- | ------------------------------------- | --------------------- |
| API_KEY             | API authentication key                | your-api-key          |
| AZURE_SPEECH_KEY    | Azure Speech Services key             | your-azure-speech-key |
| AZURE_SPEECH_REGION | Azure Speech Services region          | your-azure-region     |
| OPENAI_API_KEY      | OpenAI API key                        | your-openai-key       |
| GLADIA_API_KEY      | Gladia API key for diarization        | your-gladia-key       |
| API_BASE_URL        | Internal API base URL                 | http://localhost:8000 |
| NGROK_AUTHTOKEN     | Ngrok authentication token (optional) | your-ngrok-auth-token |

## Database

The project uses SQLite as the database, stored in `data/sql_app.db`. The database file is automatically created when the application starts.

## Docker Commands

### Build and Run

```bash
# Build and start containers
docker-compose up --build

# Run in background
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f
```

### Data Persistence

The project uses Docker volumes for SQLite database persistence:

```bash
# Stop containers but preserve data
docker-compose down

# Stop containers and remove all data
docker-compose down -v

# List all volumes
docker volume ls

# Inspect volume details
docker volume inspect oasis_sqlite_data
```

The SQLite database is stored in a Docker volume named `sqlite_data`. This ensures that:

- Data persists between container restarts
- Data is preserved when containers are stopped
- Data is only removed when explicitly using the `-v` flag

### Container Management

```bash
# List running containers
docker ps

# Enter container shell
docker exec -it oasis_app /bin/bash

# Restart container
docker-compose restart fastapi
```

## API Endpoints

All endpoints require API Key authentication via the `X-API-Key` header.

### Audio

- `POST /api/v1/audio/upload` - Upload new audio file

### Transcription

- `GET /api/v1/transcription/latest/analyze` - Analyze latest transcription using OpenAI

### Motion

- `POST /api/v1/motion/upload` - Upload motion data

### Vision

- `POST /api/v1/vision/upload` - Upload image data

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
