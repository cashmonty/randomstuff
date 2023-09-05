import csv
import time
import logging
from moralis import evm_api  # Assuming you have imported Moralis

# Initialize logging
logging.basicConfig(filename='wallet_profit.log', level=logging.INFO)

# Your API key
api_key = ""

# Initialize variables
chain = "eth"
uniswap_routers = ['0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', '0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD']
weth_contract = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

# Function to fetch transactions from Moralis
def get_wallet_transactions(wallet_address):
    params = {
        "chain": chain,
        "address": wallet_address
    }
    return evm_api.transaction.get_wallet_transactions_verbose(api_key=api_key, params=params)

# Read wallet addresses from CSV
wallet_addresses = []
with open('CashWallets.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        wallet_addresses.append(row[0])

# Prepare CSV output
with open('profitability_results.csv', 'w', newline='') as csvfile:
    fieldnames = ['Wallet Address', 'Total Realized Profit']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through each wallet address
    for wallet_address in wallet_addresses:
        transactions = {}

        # Fetch transactions for the wallet
        result = get_wallet_transactions(wallet_address)

        # Loop through transactions
        for tx in result['result']:
            # Internal transactions for WETH received back to the wallet
            if tx['to_address'] == wallet_address and tx['from_address'] == weth_contract:
                transactions.setdefault('received_weth', 0)
                transactions['received_weth'] += float(tx['value']) / 1e18

            # Decoded transactions for WETH transferred to Uniswap router
            if 'decoded_call' in tx and tx['decoded_call']['signature'] == 'transfer(address,uint256)':
                if 'decoded_call' in tx and tx['decoded_call'] is not None:  # Added check here
                    if tx['to_address'] in uniswap_routers and tx['from_address'] == weth_contract:
                        transactions.setdefault('spent_weth', 0)
                        transactions['spent_weth'] += float(tx['value']) / 1e18

        # Calculate profit
        total_realized_profit = transactions.get('received_weth', 0) - transactions.get('spent_weth', 0)

        # Write to CSV
        writer.writerow({
            'Wallet Address': wallet_address,
            'Total Realized Profit': total_realized_profit
        })

        logging.info(f"Processed wallet address {wallet_address}")

        # Pause to avoid rate-limiting
        time.sleep(2)
