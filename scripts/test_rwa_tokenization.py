import os
import json
import time
import sys
import requests
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Global variables to store XRPL DID and Wallet (loaded from gcb_kyc_data.json)
INVESTOR_DATA = {} # Will store mapping of investor_id to their data

def load_investor_data():
    global INVESTOR_DATA
    file_path = "gcb_kyc_data.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            INVESTOR_DATA = {inv['investor_id']: inv for inv in data['investors']}
        print(f"Loaded investor data for {len(INVESTOR_DATA)} investors.")
    else:
        print(f"Error: {file_path} not found. Please run xrpl_did_kyc_setup.py first.")
        sys.exit(1)

def load_contract_abi():
    try:
        from solcx import compile_standard
        CONTRACT_PATH = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'GCBToken.sol')
        with open(CONTRACT_PATH, 'r') as f:
            contract_content = f.read()
        compiled_sol = compile_standard(
            {"language": "Solidity", "sources": {CONTRACT_PATH: {"content": contract_content}},
             "settings": {"outputSelection": {"*": {"*": ["abi"]}}}},
            solc_version="0.8.20",
            allow_paths=[os.path.dirname(CONTRACT_PATH), os.path.join(os.path.dirname(__file__), '..', 'node_modules', '@openzeppelin')]
        )
        return compiled_sol['contracts'][CONTRACT_PATH]['GCBToken']['abi']
    except Exception as e:
        print(f"Could not compile or load ABI for GCBToken: {e}. Please ensure contracts/GCBToken.sol is correct.")
        sys.exit(1)


def test_rwa_tokenization():
    print("--- Testing GCB Fractional Ownership Tokenization ---")

    load_investor_data()

    w3 = Web3(Web3.HTTPProvider(config.EVM_NETWORK_URL))
    if not w3.is_connected():
        print(f"Error: Could not connect to EVM network at {config.EVM_NETWORK_URL}")
        sys.exit(1)
    print(f"Connected to EVM network (chain ID: {w3.eth.chain_id}).")

    deployer_private_key = config.EVM_DEPLOYER_PRIVATE_KEY
    if not deployer_private_key.startswith('0x'):
        deployer_private_key = '0x' + deployer_private_key
    deployer_account = w3.eth.account.from_key(deployer_private_key)
    w3.eth.default_account = deployer_account.address # Set default sender for transactions

    print(f"GCB Owner (Deployer) Address: {deployer_account.address}")

    # Access the GCBToken contract using its ABI and address
    gcb_token_contract_address = config.ACCESS_CONTROL_CONTRACT_ADDRESS
    if not gcb_token_contract_address:
        print("ERROR: ACCESS_CONTROL_CONTRACT_ADDRESS (GCBToken address) not set in .env. Please run deploy_gcb_token.py first.")
        sys.exit(1)

    gcb_token_abi = load_contract_abi()
    gcb_token_contract = w3.eth.contract(
        address=gcb_token_contract_address,
        abi=gcb_token_abi
    )
    print(f"Connected to GCBToken contract at: {gcb_token_contract_address}")

    # --- STEP 1: Simulate Investor EVM Address Linking to XRPL DID ---
    # In a real system, each investor would have their own EVM keypair.
    # For this prototype, we'll assign dummy EVM addresses or reuse the deployer's for simplicity
    # but the logic implies separate identities.
    # We'll generate fresh EVM addresses for investors to represent distinct entities.
    print("\n--- Simulating Investor EVM Address Linking & KYC Attestation ---")
    investor_evm_wallets = {}
    for inv_id, inv_data in INVESTOR_DATA.items():
        # Generate a new EVM wallet for each investor for demo purposes
        # In real-world, investors use their own wallets
        investor_wallet = w3.eth.account.create()
        investor_evm_wallets[inv_id] = investor_wallet

        # Update investor_data with the generated EVM address
        inv_data['evm_address_linked'] = investor_wallet.address
        print(f"  Investor {inv_id} (DID: {inv_data['xrpl_did']}) assigned EVM Address: {inv_data['evm_address_linked']}")

        # Simulate KYC attestation request to the Oracle
        print(f"  Requesting KYC attestation from Oracle for Investor {inv_id}...")
        try:
            oracle_response = requests.post(
                f"http://localhost:{config.ORACLE_PORT}/attest-kyc",
                json={
                    "xrplDID": inv_data['xrpl_did'],
                    "investorEVMAddress": inv_data['evm_address_linked']
                }
            )
            oracle_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            print(f"  Oracle response for Investor {inv_id}: {oracle_response.json()}")

            if oracle_response.json().get('success'):
                print(f"  Oracle successfully processed KYC attestation for Investor {inv_id}.")
                # Wait for the EVM transaction from the oracle to be mined
                # We need to explicitly check for the transaction from the oracle
                tx_hash = oracle_response.json().get('tx_hash')
                if tx_hash:
                    try:
                        w3.eth.wait_for_transaction_receipt(Web3.to_bytes(hexstr=tx_hash))
                        print(f"  Oracle's EVM transaction confirmed for Investor {inv_id}.")
                    except TransactionNotFound:
                        print(f"  Warning: Oracle's transaction {tx_hash} not found or timed out. May need more time.")
                else:
                    print(f"  No transaction hash received from Oracle for Investor {inv_id}.")

            else:
                print(f"  Oracle failed to process KYC attestation for Investor {inv_id}: {oracle_response.json().get('error')}")

        except requests.exceptions.ConnectionError:
            print(f"  Error: Could not connect to Oracle at http://localhost:{config.ORACLE_PORT}. Make sure `gcb_kyc_oracle.py` is running!")
            sys.exit(1)
        except Exception as e:
            print(f"  Error communicating with oracle for Investor {inv_id}: {e}")
        time.sleep(1) # Small delay between requests

    print("\n--- Verifying KYC Status on GCBToken Contract ---")
    for inv_id, inv_data in INVESTOR_DATA.items():
        is_whitelisted = gcb_token_contract.functions.isWhitelisted(inv_data['evm_address_linked']).call()
        print(f"  Investor {inv_id} (EVM: {inv_data['evm_address_linked']}) whitelisted status: {is_whitelisted} (Expected: {inv_data['kyc_approved']})")


    # --- STEP 2: Initial Token Allocation (GCB Owner to Investors) ---
    print("\n--- Initial GCB Token Allocation from Owner to Investors ---")
    owner_balance = gcb_token_contract.functions.balanceOf(deployer_account.address).call()
    print(f"GCB Owner's initial token balance: {w3.from_wei(owner_balance, 'ether')} GCBS")

    # Allocate 1000 tokens to each whitelisted investor
    tokens_to_allocate_per_investor = w3.to_wei(1000, 'ether')
    
    for inv_id, inv_data in INVESTOR_DATA.items():
        if inv_data['kyc_approved']:
            print(f"  Allocating {w3.from_wei(tokens_to_allocate_per_investor, 'ether')} GCBS to Investor {inv_id} ({inv_data['evm_address_linked']})...")
            try:
                nonce = w3.eth.get_transaction_count(deployer_account.address)
                tx_hash = gcb_token_contract.functions.transfer(
                    inv_data['evm_address_linked'],
                    tokens_to_allocate_per_investor
                ).transact({'from': deployer_account.address, 'nonce': nonce})
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print(f"    Allocation successful. Tx Hash: {tx_hash.hex()}")
                else:
                    print(f"    Allocation FAILED. Tx Hash: {tx_hash.hex()}")
            except Exception as e:
                print(f"    Error allocating tokens to Investor {inv_id}: {e}")
        else:
            print(f"  Skipping allocation to Investor {inv_id} (not KYC approved).")
        time.sleep(1) # Small delay

    print("\n--- Verifying Investor Balances After Allocation ---")
    for inv_id, inv_data in INVESTOR_DATA.items():
        balance = gcb_token_contract.functions.balanceOf(inv_data['evm_address_linked']).call()
        print(f"  Investor {inv_id} ({inv_data['evm_address_linked']}) balance: {w3.from_wei(balance, 'ether')} GCBS")


    # --- STEP 3: Test Token Transfers (Whitelisted vs. Non-Whitelisted) ---
    print("\n--- Testing Token Transfers Between Investors ---")
    # Find a whitelisted and a non-whitelisted investor for transfer tests
    whitelisted_investor = next((inv for inv in INVESTOR_DATA.values() if inv['kyc_approved']), None)
    non_whitelisted_investor = next((inv for inv in INVESTOR_DATA.values() if not inv['kyc_approved']), None)

    if whitelisted_investor:
        print(f"\nAttempting transfer from whitelisted investor {whitelisted_investor['investor_id']} to another whitelisted investor...")
        # Need a second whitelisted investor for this test
        second_whitelisted_investor = next((inv for inv_id, inv in INVESTOR_DATA.items() if inv['kyc_approved'] and inv['investor_id'] != whitelisted_investor['investor_id']), None)
        if second_whitelisted_investor:
            transfer_amount = w3.to_wei(100, 'ether')
            try:
                # Need to use the sending investor's wallet
                sender_wallet = w3.eth.account.from_key(investor_evm_wallets[whitelisted_investor['investor_id']].key)
                nonce = w3.eth.get_transaction_count(sender_wallet.address)
                tx = gcb_token_contract.functions.transfer(
                    second_whitelisted_investor['evm_address_linked'],
                    transfer_amount
                ).build_transaction({
                    'chainId': w3.eth.chain_id,
                    'gasPrice': w3.eth.gas_price,
                    'from': sender_wallet.address,
                    'nonce': nonce
                })
                signed_tx = sender_wallet.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print(f"  SUCCESS: Whitelisted investor transfer successful. Tx Hash: {tx_hash.hex()}")
                else:
                    print(f"  FAILURE: Whitelisted investor transfer failed. Tx Hash: {tx_hash.hex()}")
            except Exception as e:
                print(f"  ERROR: Whitelisted investor transfer failed: {e}")
        else:
            print("  Not enough whitelisted investors for transfer test.")

    if non_whitelisted_investor and whitelisted_investor:
        print(f"\nAttempting transfer from whitelisted investor to non-whitelisted investor {non_whitelisted_investor['investor_id']} (EXPECTED TO FAIL)...")
        transfer_amount = w3.to_wei(50, 'ether')
        try:
            sender_wallet = w3.eth.account.from_key(investor_evm_wallets[whitelisted_investor['investor_id']].key)
            nonce = w3.eth.get_transaction_count(sender_wallet.address)
            tx = gcb_token_contract.functions.transfer(
                non_whitelisted_investor['evm_address_linked'],
                transfer_amount
            ).build_transaction({
                'chainId': w3.eth.chain_id,
                'gasPrice': w3.eth.gas_price,
                'from': sender_wallet.address,
                'nonce': nonce
            })
            signed_tx = sender_wallet.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            # It should revert, so waiting for receipt might take long or fail.
            # A more robust way to test reverts is to use a local ganache or hardhat network.
            # For testnet, we send and check status.
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt.status == 0:
                print(f"  SUCCESS (expected): Transfer to non-whitelisted failed as expected. Tx Hash: {tx_hash.hex()}")
            else:
                print(f"  FAILURE (unexpected): Transfer to non-whitelisted succeeded. Tx Hash: {tx_hash.hex()}")
        except ContractLogicError as e:
             print(f"  SUCCESS (expected): Transfer to non-whitelisted failed with contract logic error: {e}")
        except Exception as e:
            print(f"  ERROR: Transfer to non-whitelisted investor failed: {e}")


    # --- STEP 4: Simulate Income Distribution ---
    print("\n--- Simulating GCB Income Distribution ---")
    income_amount_wei = w3.to_wei(5, 'ether') # 5 ETH worth of income
    print(f"Distributing simulated income of {w3.from_wei(income_amount_wei, 'ether')} ETH...")
    try:
        nonce = w3.eth.get_transaction_count(deployer_account.address)
        tx_hash = gcb_token_contract.functions.distributeIncome(income_amount_wei).transact({
            'from': deployer_account.address,
            'nonce': nonce
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"Income distribution initiated successfully. Tx Hash: {tx_hash.hex()}")
            # The event log will show the distribution.
            # Off-chain systems would read this event to perform actual payouts.
        else:
            print(f"Income distribution failed. Tx Hash: {tx_hash.hex()}")
    except Exception as e:
        print(f"Error during income distribution: {e}")

if __name__ == "__main__":
    test_rwa_tokenization()
