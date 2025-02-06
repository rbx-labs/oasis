import asyncio
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(signum, frame):
    logger.info(f'Received signal {signum}, performing cleanup...')
    # Add your cleanup code here (e.g., closing connections, saving state)
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)

async def main():
    while True:
        logger.info("Hello, world!")
        await asyncio.sleep(1)

asyncio.run(main())