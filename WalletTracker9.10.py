from decimal import Decimal
import csv
import asyncio
import os
from web3 import Web3
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv("wallettracker.env")

# Use environment variables
infura_project_id = os.getenv("INFURA_PROJECT_ID")
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Web3 with Infura project ID
w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_project_id}'))

# Read wallet addresses from CSV file and convert to checksum format
wallet_addresses = []
with open('CEWallets.csv', 'r') as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        checksum_address = Web3.to_checksum_address(row[0].lower())
        wallet_addresses.append(checksum_address)

# Generate the event signature hash for the 'Swap' event
event_signature_hash = w3.keccak(text="Swap(address,uint256,uint256,uint256,uint256)").hex()

# Create a custom event filter
event_filter_params = {
    "fromBlock": "latest",
    "address": wallet_addresses,
    "topics": [event_signature_hash]
}

event_filter = w3.eth.filter(event_filter_params)

async def log_loop(poll_interval, context):
    while True:
        for event in event_filter.get_new_entries():
            tx_hash = event['transactionHash'].hex()
            tx = w3.eth.getTransaction(tx_hash)
            logger.info(f"API Response: {tx}")

            if tx['from'].lower() in wallet_addresses or tx['to'].lower() in wallet_addresses:
                value_ether = Decimal(tx['value']) / Decimal(10 ** 18)
                message = f"""Swap Event Detected!
                - From: {tx['from']}
                - To: {tx['to']}
                - Value: {value_ether} Ether
                - Tx Hash: {tx['hash'].hex()}
                """
                await context.bot.send_message(chat_id='-1001976509806', text=message, parse_mode=ParseMode.MARKDOWN_V2)
        await asyncio.sleep(poll_interval)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Monitoring started.")
    await log_loop(10, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Call CashMontee HE HE HE")

def main():
    application = (
        Application.builder()
        .token(telegram_bot_token)
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
