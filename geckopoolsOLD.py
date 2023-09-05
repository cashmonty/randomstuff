import requests
import logging
import re  # Regular Expression module
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

latest_pools = []

async def check_new_pools(context: ContextTypes.DEFAULT_TYPE):
    global latest_pools
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/networks/eth/pools",
                                headers={"Accept": "application/json;version=20230302"})
        if response.status_code == 200:
            new_data = response.json().get('data', [])
            
            if new_data and new_data != latest_pools:
                for pool in new_data:
                    name = pool['attributes'].get('name', 'Unknown')
                    address = pool['attributes'].get('address', 'Unknown')
                    token_price_usd = pool['attributes'].get('token_price_usd', 'Unknown')
                
                    # Skip pools with "USDC" or "usdc" in the name
                    if "USDC" in name or "usdc" in name:
                        continue  # This line is now correctly indented
                
                    # Escape special characters for Markdown V2
                    name = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', name)
                    address = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', address)
                    token_price_usd = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(token_price_usd))
                
                    # Create hyperlink for the contract address
                    hyperlink = f"[{address}](https://www.geckoterminal.com/eth/pools/{address})"
                
                    message = f"Top Pool:\nName: {name}\nContract Address: {hyperlink}\nToken Price USD: {token_price_usd}"
                
                    await context.bot.send_message(chat_id='', text=message, parse_mode=ParseMode.MARKDOWN_V2)
                
                latest_pools = new_data  # This line should only appear once
    except Exception as e:
        logger.error(f"Error in check_new_pools: {e}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token('').build()
        
        job_queue = application.job_queue

        if job_queue is not None:
            job_queue.run_repeating(check_new_pools, interval=120)  # Run every 2 minutes
        else:
            logger.error("JobQueue is not initialized.")
        
        application.run_polling()
    except Exception as e:
        logger.error(f"Error in main: {e}")
