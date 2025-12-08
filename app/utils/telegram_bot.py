# Telegram functionality has been removed
# This file is kept for backward compatibility but does nothing

import logging

logger = logging.getLogger("telegram_bot")

def send_telegram_message(message: str):
    """Deprecated: Telegram functionality has been removed"""
    logger.debug(f"Telegram disabled - message not sent: {message[:50]}...")
    pass
