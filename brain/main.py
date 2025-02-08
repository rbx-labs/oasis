import asyncio
import logging
import signal
import sys
import aiohttp
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def handler(signum, frame):
    logger.info(f'Received signal {signum}, performing cleanup...')
    # Add your cleanup code here (e.g., closing connections, saving state)
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)

async def fetch_speaker_data(session):
    internal_url = os.getenv('INTERNAL_URL_BASE')
    api_key = os.getenv('API_KEY')
    
    try:
        headers = {'X-API-Key': api_key} if api_key else {}
        url = f"{internal_url}/api/v1/transcription/latest/analyze"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Speaker API response: {data}")
            else:
                logger.error(f"Failed to fetch speaker data. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching speaker data: {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await fetch_speaker_data(session)
            await asyncio.sleep(60)  # Wait for 60 seconds before next request

asyncio.run(main())