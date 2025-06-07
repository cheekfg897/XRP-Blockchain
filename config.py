# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# XRPL DevNet/Testnet Configuration
XRPL_NETWORK_URL = os.getenv('XRPL_NETWORK_URL', 'wss://s.devnet.rippletest.net:51233')
XRPL_MASTER_ACCOUNT_SEED = os.getenv('XRPL_MASTER_ACCOUNT_SEED', 'sEdV4LdYdMhR1z89Yv2jQp7oXn6mP3k5') # REPLACE with your testnet seed

# XRPL EVM Sidechain DevNet/Testnet Configuration
EVM_NETWORK_URL = os.getenv('EVM_NETWORK_URL', 'https://rpc-evm-sidechain.xrpl.org')
EVM_DEPLOYER_PRIVATE_KEY = os.getenv('EVM_DEPLOYER_PRIVATE_KEY', '0xac0974bec39a17e36ba4a6b4d238ff944bac478cbfd5c6439e0da1609756bde0') # REPLACE with a test private key for EVM
# This key needs test XRP to pay for gas on the EVM sidechain.

# Axelar Testnet Configuration (Simplified for prototype)
# In a real scenario, you'd integrate with Axelar SDK for GMP.
AXELAR_GATEWAY_ADDRESS = os.getenv('AXELAR_GATEWAY_ADDRESS', "0xF6B117A166A8E196c09b119159046c430B722421") # Placeholder

# Oracle Configuration
ORACLE_PORT = int(os.getenv('ORACLE_PORT', 3000))

# Smart Contract Address (will be set after deployment)
ACCESS_CONTROL_CONTRACT_ADDRESS = os.getenv('ACCESS_CONTROL_CONTRACT_ADDRESS', None)

# Simulation Data (for DIDs and VCs)
SIMULATION_PERMISSIONS = ['premium_access', 'admin_dashboard_access', 'kyc_verified']
