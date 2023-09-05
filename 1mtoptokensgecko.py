import requests
import logging
import re  # Regular Expression module
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

latest_tokens = []

async def check_low_fdv_tokens(context: ContextTypes.DEFAULT_TYPE):
    global latest_tokens
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/networks/eth/tokens",
                                headers={"Accept": "application/json;version=20230302"})
        if response.status_code == 200:
            new_data = response.json().get('data', [])
            
            if new_data and new_data != latest_tokens:
                for token in new_data:
                    top_pools = token['relationships'].get('top_pools', {}).get('data', [])
                    
                    if top_pools:
                        name = token['attributes'].get('name', 'Unknown')
                        address = token['attributes'].get('address', 'Unknown')
                        
                        # Escape special characters for Markdown V2
                        name = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', name)
                        address = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', address)
                        
                        # Create hyperlink for the contract address
                        hyperlink = f"[{address}](https://www.geckoterminal.com/eth/tokens/{address})"
                        
                        message = (
                        f"*Token in Top Pool:*\n"
                        f"**{name}**\n"  # Making the token name bold
                        f"Contract Address: [{address}](https://www.geckoterminal.com/eth/tokens/{address})\n"
                        f"Symbol: {token['attributes'].get('symbol', 'Unknown')}\n"
                        f"FDV USD: {token['attributes'].get('fdv_usd', 'Unknown')}\n"
                        f"Total Reserve in USD: {token['attributes'].get('total_reserve_in_usd', 'Unknown')}\n"
                        f"24h Volume USD: {token['attributes'].get('volume_usd', {}).get('h24', 'Unknown')}\n"

                        )

                        
                        await context.bot.send_message(chat_id='', text=message, parse_mode=ParseMode.MARKDOWN_V2)
                
                latest_tokens = new_data
    except Exception as e:
        logger.error(f"Error in check_low_fdv_tokens: {e}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token('').build()
        
        job_queue = application.job_queue

        if job_queue is not None:
            job_queue.run_repeating(check_low_fdv_tokens, interval=120)  # Run every 2 minutes
        else:
            logger.error("JobQueue is not initialized.")
        
        application.run_polling()
    except Exception as e:
        logger.error(f"Error in main: {e}")
