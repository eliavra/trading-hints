import asyncio
import pandas as pd
from ib_insync import IB, Trade, Fill, Execution
import datetime
import os

def fetch_and_export_transactions(
    host='127.0.0.1', 
    port=4001, 
    client_id=1, 
    output_file='ib_transactions.csv'
):
    """
    Connects to IB Gateway/TWS, fetches executions (fills), and exports them to CSV. 
    
    Args:
        host: IP address of the IB Gateway/TWS (default 127.0.0.1)
        port: Port number (4001 for IB Gateway Live, 7496 for TWS Live, 4002/7497 for Paper)
        client_id: Unique ID for this API client connection.
        output_file: Path to save the CSV report.
    """
    ib = IB()
    
    print(f"Connecting to IBKR (Host: {host}, Port: {port}, ClientID: {client_id})...")
    try:
        ib.connect(host, port, clientId=client_id)
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to IBKR: {e}")
        print("Ensure IB Gateway or TWS is running and API connections are enabled.")
        return

    try:
        # Request all executions (fills)
        # An empty ExecutionFilter() fetches all executions matching the client
        print("Fetching executions (this may take a moment)...")
        fills = ib.fills()  # Returns a list of (Contract, Execution, CommissionReport) tuples
        
        print(f"Retrieved {len(fills)} execution records.")

        if not fills:
            print("No transactions found.")
            return

        # Process data into a list of dictionaries
        data = []
        for fill in fills:
            contract = fill.contract
            exec = fill.execution
            comm = fill.commissionReport

            row = {
                'Date': exec.time.strftime('%Y-%m-%d %H:%M:%S'),
                'Symbol': contract.symbol,
                'SecType': contract.secType,
                'Exchange': contract.exchange,
                'Action': exec.side,  # BOT (Buy) or SLD (Sell)
                'Quantity': exec.shares,
                'Price': exec.price,
                'Currency': contract.currency,
                'Commission': comm.commission if comm else 0.0,
                'CommCurrency': comm.currency if comm else '',
                'RealizedPNL': comm.realizedPNL if comm else 0.0,
                'OrderID': exec.orderId,
                'ExecID': exec.execId,
                'Account': exec.acctNumber,
            }
            data.append(row)

        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by Date descending
        df.sort_values(by='Date', ascending=False, inplace=True)

        # Export to CSV
        output_path = os.path.join(os.getcwd(), output_file)
        df.to_csv(output_path, index=False)
        print(f"✅ Report saved to: {output_path}")
        print("\nFirst 5 rows:")
        print(df.head())

    except Exception as e:
        print(f"An error occurred during data fetch: {e}")
    finally:
        ib.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    # Defaulting to IB Gateway Live port (4001). 
    # Change to 4002 for Paper Trading or 7496 for TWS Live.
    import argparse
    parser = argparse.ArgumentParser(description='Export IBKR Transactions to CSV')
    parser.add_argument('--port', type=int, default=4001, help='IBKR API Port (4001=Gateway Live, 7496=TWS Live)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='IBKR API Host')
    parser.add_argument('--file', type=str, default='ib_transactions.csv', help='Output CSV filename')
    
    args = parser.parse_args()
    
    fetch_and_export_transactions(
        host=args.host, 
        port=args.port, 
        output_file=args.file
    )
