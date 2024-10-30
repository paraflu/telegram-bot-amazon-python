# telegram-bot-amazon - Python version
# Gioxx, 2024, https://github.com/gioxx/telegram-bot-amazon-python
# In all ways inspired by the original work of LucaTNT (https://github.com/LucaTNT/telegram-bot-amazon), converted to Python, updated to work with newer versions of the software.
# Credits: all this would not have been possible (in the same times) without the invaluable help of Claude 3 Sonnet.

import os
from urllib.parse import urlparse, parse_qs, urlencode

from telegram.ext import Application, CommandHandler, MessageHandler, filters

import app as AffiliateMessageHandler

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, AffiliateMessageHandler().handler))
    application.run_polling()

if __name__ == '__main__':
    main()