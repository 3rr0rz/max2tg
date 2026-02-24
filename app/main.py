import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from app.config import load_settings
from app.max_listener import create_max_client
from app.tg_handler import build_tg_app
from app.tg_sender import TelegramSender

threading.stack_size(524288)

log = logging.getLogger("max2tg")


async def main():
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=2))

    settings = load_settings()

    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        force=True,
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING if not settings.debug else logging.DEBUG)

    log.info("Debug mode: %s", "ON" if settings.debug else "OFF")

    sender = TelegramSender(settings.tg_bot_token, settings.tg_chat_id)
    await sender.start()

    client = create_max_client(
        settings.max_token, settings.max_device_id, sender,
        debug=settings.debug, reply_enabled=settings.reply_enabled,
    )

    tg_app = None
    if settings.reply_enabled:
        tg_app = build_tg_app(settings.tg_bot_token, client, settings.tg_chat_id)
        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(drop_pending_updates=True)
        log.info("Telegram polling started (reply → Max enabled)")
    else:
        log.info("Reply to Max disabled (REPLY_ENABLED=false)")

    log.info("Starting Max listener...")
    try:
        await client.run()
    finally:
        log.info("Shutting down...")
        if tg_app:
            await tg_app.updater.stop()
            await tg_app.stop()
            await tg_app.shutdown()
        await sender.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopped.")
