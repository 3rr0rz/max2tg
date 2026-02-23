import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import load_settings
from app.max_listener import create_max_client
from app.tg_sender import TelegramSender

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

log = logging.getLogger("max2tg")


async def main():
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=2))

    settings = load_settings()

    sender = TelegramSender(settings.tg_bot_token, settings.tg_chat_id)
    await sender.start()

    client = create_max_client(settings.max_token, settings.max_device_id, sender)

    log.info("Starting Max listener...")
    try:
        await client.run()
    finally:
        await sender.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopped.")
