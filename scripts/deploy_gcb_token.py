# scripts/deploy_gcb_token.py
import os
import json
import sys
from web3 import Web3
from solcx import compile_standard, install_solc

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Path to your Solidity contract
CONTRACT_PATH = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'GCBToken.sol')

def compile_contract(contract_path):
    print("Compiling Solidity contract...")
    # Ensure solc compiler is installed
    # solcx.install_solc() # Uncomment this if you don't have solc installed

    with open(contract_path, 'r') as f:
        contract_content = f.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {contract_path: {"content": contract_content}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                    }
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            },
        },
        solc_version="0.8.20",
        allow_paths=[os.path.dirname(contract_path), os.path.join(os.path.dirname(__file__), '..', 'node_modules', '@openzeppelin')]
    )
    print("Compilation successful.")
    return compiled_sol

def deploy_gcb_token():
    print("--- Deploying GCBToken to XRPL EVM Sidechain ---")

    w3 = Web3(Web3.HTTPProvider(config.EVM_NETWORK_URL))
    if not w3.is_connected():
        print(f"Error: Could not connect to EVM network at {config.EVM_NETWORK_URL}")
        sys.exit(1)
    print(f"Connected to EVM network (chain ID: {w3.eth.chain_id}).")

    deployer_private_key = config.EVM_DEPLOYER_PRIVATE_KEY
    if not deployer_private_key:
        print("Error: EVM_DEPLOYER_PRIVATE_KEY not set in .env")
        sys.exit(1)
    
    # Ensure private key starts with '0x'
    if not deployer_private_key.startswith('0x'):
        deployer_private_key = '0x' + deployer_private_key

    deployer_account = w3.eth.account.from_key(deployer_private_key)
    w3.eth.default_account = deployer_account.address

    print(f"Deployer account: {deployer_account.address}")
    balance = w3.eth.get_balance(deployer_account.address)
    print(f"Deployer balance: {w3.from_wei(balance, 'ether')} ETH (test XRP for gas)")

    if balance == 0:
        print("WARNING: Deployer account has 0 ETH. Please fund it with test XRP on the XRPL EVM Sidechain.")
        print("Visit https://xrpl.org/xrp-evm-sidechain-faucet.html to get test XRP for gas.")
        sys.exit(1)

    try:
        compiled_sol = compile_contract(CONTRACT_PATH)
        contract_name = "GCBToken"
        
        # Get bytecode and ABI
        bytecode = compiled_sol['contracts'][CONTRACT_PATH][contract_name]['evm']['bytecode']['object']
        abi = compiled_sol['contracts'][CONTRACT_PATH][contract_name]['abi']

        GCBToken_Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # Initial supply of GCB tokens (e.g., 1 million tokens, 18 decimals)
        initial_supply = w3.to_wei(1_000_000, 'ether') # 1 million tokens

        # For prototyping, deployer's address acts as the KYC Oracle
        kyc_oracle_address = deployer_account.address # Simplification for prototype

        print(f"Deploying GCBToken with initial supply {w3.from_wei(initial_supply, 'ether')} and KYC Oracle address: {kyc_oracle_address}...")

        # Get the latest nonce
        nonce = w3.eth.get_transaction_count(deployer_account.address)
        
        # Build the transaction
        transaction = GCBToken_Contract.constructor(initial_supply, kyc_oracle_address).build_transaction({
            'chainId': w3.eth.chain_id,
            'gasPrice': w3.eth.gas_price,
            'from': deployer_account.address,
            'nonce': nonce,
        })

        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=deployer_private_key)

        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Deployment transaction sent. Tx Hash: {tx_hash.hex()}")

        # Wait for the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress

        print(f"GCBToken deployed to: {contract_address}")

        # Update ACCESS_CONTROL_CONTRACT_ADDRESS in .env (or create a new variable if preferred)
        # We'll re-use ACCESS_CONTROL_CONTRACT_ADDRESS for simplicity in this example.
        with open(".env", "r") as f:
            lines = f.readlines()
        
        updated_lines = []
        found = False
        for line in lines:
            if line.strip().startswith('ACCESS_CONTROL_CONTRACT_ADDRESS='):
                updated_lines.append(f"ACCESS_CONTROL_CONTRACT_ADDRESS={contract_address}\n")
                found = True
            else:
                updated_lines.append(line)
        
        if not found:
            updated_lines.append(f"ACCESS_CONTROL_CONTRACT_ADDRESS={contract_address}\n")

        with open(".env", "w") as f:
            f.writelines(updated_lines)

        print(f"GCBToken Contract Address saved to .env: {contract_address}")

    except Exception as e:
        print(f"Error deploying contract: {e}")

if __name__ == "__main__":
    deploy_gcb_token()
