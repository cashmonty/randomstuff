import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Replace with your Bot Token from .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def profit(update, context):
    # Check if the user provided a wallet address after the /profit command
    if not context.args or len(context.args) != 1:
        update.message.reply_text("Please provide a wallet address. Usage


def profit(update, context):
    # Check if the user provided a wallet address after the /profit command
    if not context.args or len(context.args) != 1:
        update.message.reply_text("Please provide a wallet address. Usage: /profit <wallet_address>")
        return

    wallet_address = context.args[0]
    
    # Call the Syve API
    url = f"https://api.syve.ai/v1/labels/performance?address={wallet_address}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        message = (f"Total Profit: {data['total_profit']}\n"
                   f"Realized Profit: {data['realized_profit']}\n"
                   f"Unrealized Profit: {data['unrealized_profit']}\n"
                   f"Total Return: {data['total_return']}\n"
                   f"Win Rate: {data['win_rate']}")
        update.message.reply_text(message)
    else:
        update.message.reply_text("Failed to retrieve data. Please try again later.")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("profit", profit, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, profit))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
