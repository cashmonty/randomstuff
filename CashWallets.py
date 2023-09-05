import csv
import asyncio
import json
import logging
import requests
from web3 import Web3
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Web3 with HTTPProvider
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/'))

# Read wallet addresses from CSV file
wallet_addresses = []
with open('ChainEdge_Wallets.csv', 'r') as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        wallet_addresses.append(row[0].lower())  # Convert to lowercase for easier comparison

# WETH Contract Address
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH address

async def monitor_transactions(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Monitoring transactions...")
    new_block_filter = w3.eth.filter('latest')

    while True:
        for event in new_block_filter.get_new_entries():
            block = w3.eth.get_block(event, full_transactions=True)
            for tx in block['transactions']:
                if tx['to'] == WETH_ADDRESS or tx['from'] == WETH_ADDRESS:
                    if tx['to'].lower() in wallet_addresses or tx['from'].lower() in wallet_addresses:
                        message = f"Possible swap transaction detected!\nTransaction Hash: {tx['hash'].hex()}\nFrom: {tx['from']}\nTo: {tx['to']}\nValue: {tx['value']}"
                        await context.bot.send_message(chat_id='', text=message)
        await asyncio.sleep(5)  # Wait for 5 seconds before checking again

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Monitoring started.")
    while True:
        await monitor_transactions(context)
        await asyncio.sleep(10)  # Check every 10 seconds

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /start to start monitoring.")

def main() -> None:
    application = (
        Application.builder()
        .token("")
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
