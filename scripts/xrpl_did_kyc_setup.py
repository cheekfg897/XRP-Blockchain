import asyncio
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.utils import drops_to_xrp
import json
import os
import sys
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

async def setup_xrpl_did_kyc_layer(num_investors=3):
    client = AsyncWebsocketClient(config.XRPL_NETWORK_URL)
    await client.open()

    print("--- Setting up XRPL Layer (DID & KYC Simulation) ---")

    gcb_kyc_data = {"investors": []}

    try:
        for i in range(num_investors):
            print(f"\nGenerating XRPL Wallet for Investor {i+1} (via faucet)...")
            wallet = await generate_faucet_wallet(client, debug=True)
            print(f"Generated XRPL Wallet Address: {wallet.address}")
            print(f"Wallet Seed: {wallet.seed}")
            # print(f"Initial balance: {drops_to_xrp(await client.request(AccountInfo(account=wallet.address))['result']['account_data']['Balance'])} XRP")

            # Simulate DID (using XRPL address as DID)
            xrpl_did = f"did:xrpl:{wallet.address}"
            print(f"Simulated XRPL DID: {xrpl_did}")

            # Simulate KYC status: roughly 60% approved, 40% not
            kyc_approved = random.choices([True, False], weights=[0.6, 0.4], k=1)[0]
            print(f"Simulated KYC Status: {'APPROVED' if kyc_approved else 'NOT APPROVED'}")

            investor_data = {
                "investor_id": i + 1,
                "xrpl_did": xrpl_did,
                "xrpl_wallet_seed": wallet.seed, # Store for full prototype; in real app, highly sensitive
                "kyc_approved": kyc_approved,
                "evm_address_linked": None # This will be filled later by test script
            }
            gcb_kyc_data["investors"].append(investor_data)

        # Save this info for the oracle and other scripts
        file_path = "gcb_kyc_data.json"
        with open(file_path, "w") as f:
            json.dump(gcb_kyc_data, f, indent=4)
        print(f"\nXRPL DID and KYC simulation data saved to {file_path}")

    except Exception as e:
        print(f"Error during XRPL DID/KYC setup: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(setup_xrpl_did_kyc_layer(num_investors=4)) # Setup 4 investors for demo

