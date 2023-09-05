from moralis import evm_api
from decimal import Decimal
import csv
import time

# Your API key
api_key = ""

# Initialize variables
chain = "eth"

# Read wallet addresses from CSV
wallet_addresses = []
try:
    with open('CashWallets.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            wallet_addresses.append(row[0])
except FileNotFoundError:
    print("CSV file not found.")
    exit()

# Prepare CSV output
try:
    with open('profitability_results.csv', 'w', newline='') as csvfile:
        fieldnames = ['Wallet Address', 'Total Profit', 'Profitability %']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Loop through each wallet address
        for wallet_address in wallet_addresses:
            params = {
                "chain": chain,
                "address": wallet_address
            }

            # Initialize counters
            total_profit = 0.0
            total_trades = 0
            profitable_trades = 0

            # Fetch ERC20 transfers for the wallet
            try:
                result = evm_api.token.get_wallet_token_transfers(
                    api_key=api_key,
                    params=params,
                )
            except Exception as e:
                print(f"Error fetching ERC20 transfers for {wallet_address}: {e}")
                continue

            # Loop through transactions
            for tx in result['result']:
                total_trades += 1  # Increment total trades
                block_number = tx['block_number']
                token_address = tx['to_address'] if tx['to_address'] != wallet_address else tx['from_address']

                # Fetch historical token price at the time of the transaction
                params = {
                    "address": token_address,
                    "chain": chain,
                    "to_block": int(block_number)  # Convert to integer
                }

                try:
                    historical_price = evm_api.token.get_token_price(
                        api_key=api_key,
                        params=params,
                    )['usdPrice']
                except Exception as e:
                    print(f"Error fetching historical price for {token_address}: {e}")
                    print("Skipping this token.")
                    continue

                # Calculate profit based on the historical price and transaction value
                value_in_ether = float(tx['value']) / 1e18  # Convert value from Wei to Ether
                profit = value_in_ether * historical_price  # Calculate profit in USD
                total_profit += profit  # Accumulate total profit

                if profit > 0:
                    profitable_trades += 1  # Increment profitable trades

            # Calculate profitability percentage
            profitability_percent = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

            # Write results to CSV
            writer.writerow({
                'Wallet Address': wallet_address,
                'Total Profit': total_profit,
                'Profitability %': profitability_percent
            })

            # Pause to avoid rate-limiting
            time.sleep(60)

except Exception as e:
    print(f"Error writing to CSV: {e}")
