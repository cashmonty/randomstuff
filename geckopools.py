import requests
import logging
import time
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
import json

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to check for new pools
def check_new_pools(context: CallbackContext) -> None:
    try:
        time.sleep(2)  # Rate-limiting
        response = requests.get("https://api.geckoterminal.com/api/v2/networks/eth/pools",
                                headers={"Accept": "application/json;version=20230302"})
        if response.status_code == 200:
            new_data = response.json().get('data', [])
            latest_pools = context.bot_data.get('latest_pools', [])
            
            if new_data and new_data != latest_pools:
                for pool in new_data:
                    name = pool['attributes'].get('name', 'Unknown')
                    address = pool['attributes'].get('address', 'Unknown')
                    token_price_usd = pool['attributes'].get('token_price_usd', 'Unknown')
                    
                    message = f"Top Pool:\nName: {name}\nContract Address: {address}\nToken Price USD: {token_price_usd}"
                    context.bot.send_message(chat_id='', text=message)
                
                context.bot_data['latest_pools'] = new_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in check_new_pools: {e}")

# Main function
if __name__ == '__main__':
    try:
        # Initialize ApplicationBuilder
        app_builder = ApplicationBuilder().token('')
        
        # Debug: Check if self._job_queue is properly initialized
        if hasattr(app_builder, '_job_queue'):
            print("self._job_queue is initialized in ApplicationBuilder.")
        else:
            print("self._job_queue is NOT initialized in ApplicationBuilder.")
        
        application = app_builder.build()
        
        if application is not None:
            print("Application is initialized.")  # Debug print
            
            job_queue = application.job_queue
            
            # Debug: Check if job_queue is properly initialized
            if job_queue is not None:
                print("JobQueue is initialized.")  # Debug print
                job_queue.run_repeating(check_new_pools, interval=30)
            else:
                logger.error("JobQueue is not initialized.")
            
            application.run_polling()
        else:
            logger.error("Application is not initialized.")
    except Exception as e:
        logger.error(f"Error in main: {e}")
