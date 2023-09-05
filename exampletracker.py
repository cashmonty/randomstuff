import csv
import asyncio
from decimal import Decimal
from telegram import Update, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

wallet_addresses = []
with open('ChainEdge_Wallets.csv', 'r') as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        wallet_addresses.append(row[0].lower())

async def log_loop(event_filter, poll_interval, context):
    while True:
        for event in await event_filter.get_new_entries():
            block = await w3.eth.get_block(event)
            for tx_hash in block['transactions']:
                tx = await w3.eth.get_transaction(tx_hash)
                logger.info(f"API Response: {tx}")

                if tx['from'].lower() in wallet_addresses or tx['to'].lower() in wallet_addresses:
                    value_ether = Decimal(tx['value']) / Decimal(10**18)
                    hyperlink_from = f"[{tx['from']}](https://app.zerion.io/{tx['from']}/overview)"
                    hyperlink_to = f"[{tx['to']}](https://app.zerion.io/{tx['to']}/overview)"
                    
                    message = f"""Transaction Detected!
                    - From: {hyperlink_from}
                    - To: {hyperlink_to}
                    - Value: {value_ether} Ether
                    - Gas: {tx['gas']}
                    - Gas Price: {tx['gasPrice']} Wei
                    - Nonce: {tx['nonce']}
                    - Tx Hash: {tx['hash'].hex()}
                    """
                    
                    await context.bot.send_message(chat_id='-1001976509806', text=message, parse_mode=ParseMode.MARKDOWN_V2)
        await asyncio.sleep(poll_interval)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Monitoring started.")
    new_block_filter = w3.eth.filter('latest')
    await log_loop(new_block_filter, 10, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to start monitoring.")

def main():
    application = (
        Application.builder()
        .token("6673913101:AAHnW3qnZ5ppGDqREBqlbYRy8K5ihAYThOs")
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(application.run_polling(allowed_updates=Update.ALL_TYPES))
    finally:
        loop.close()

if __name__ == "__main__":
    main()
