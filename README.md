Markdown


# Tokenized Good Class Bungalow (GCB) Fractional Ownership with XRPL-DID-Based KYC (Python Edition)

## Project Overview

This prototype demonstrates a decentralized approach to **Real-World Asset (RWA) tokenization**, specifically focusing on fractional ownership of a high-value asset like a Good Class Bungalow (GCB) in Singapore. It combines the strengths of the **XRPL EVM Sidechain** for token issuance and access control with the **native XRPL's Decentralized Identifier (DID)** capabilities for investor KYC/AML verification.

A key innovation is the use of an off-chain **Python Oracle** that simulates **Axelar's General Message Passing (GMP)**, bridging the identity verification from the XRPL to the EVM Sidechain. This ensures that only KYC-approved investors can hold and transfer the fractional GCB ownership tokens. The prototype also includes a mechanism for simulating income distribution to token holders.

This project is entirely back-end focused, showcasing the intricate smart contract logic and inter-blockchain communication through command-line scripts and console output.

## Problem Solved

Traditional real estate fractionalization often relies on centralized platforms and opaque investor vetting processes. This project addresses the need for:
1.  **Transparent Fractional Ownership:** Representing GCB shares as fungible ERC-20 tokens.
2.  **On-Chain Compliance:** Enforcing KYC/AML rules directly within the smart contract, preventing transfers to non-approved addresses.
3.  **Cross-Chain Identity Verification:** Leveraging XRPL DIDs for identity management and connecting it to EVM-based assets.
4.  **Automated Earnings Distribution:** Providing a framework for distributing rental income or other earnings to token holders.

## Architecture


+-------------------+ +-------------------------------------+ +---------------------------+
| XRPL DevNet | | Off-Chain GCB KYC Oracle (Python) | | XRPL EVM Sidechain |
| | | (Simulating Axelar Bridge) | | |
| - DID Generation | <--->| - Listens for EVM Investor Requests | <--->| - GCBToken.sol (ERC-20) |
| - KYC VC (Simulated) | | - Resolves XRPL DIDs/KYC status | | - Permissioned Transfers|
| | | - Sends KYC status to EVM via EVM tx| | - Income Distribution |
+-------------------+ +-------------------------------------+ +---------------------------+
^
| HTTP/API (Prototype Sim)
v
+--------------------------+
| Python Scripts |
| - xrpl_did_kyc_setup.py|
| - test_rwa_tokenization|
+--------------------------+



## Core Components

1.  **XRPL Layer (DevNet/Testnet):**
    * **Simulated DID & KYC VC:** `xrpl-py` is used to create XRPL test accounts, whose addresses serve as DIDs. A local JSON file (`gcb_kyc_data.json`) stores a simulated Verifiable Credential (VC) for each DID, indicating whether its KYC status is `true` or `false`.
2.  **XRPL EVM Sidechain Layer (DevNet/Testnet):**
    * **`GCBToken.sol` Smart Contract:** An ERC-20 token contract. It enforces a whitelist for transfers, meaning only addresses that have been approved by the KYC Oracle can send or receive `GCBS` tokens. It also includes a function to simulate the distribution of income to token holders.
3.  **Off-Chain GCB KYC Oracle (Python Flask Application):**
    * This Flask server acts as the trusted attester for KYC status. It loads the `gcb_kyc_data.json` and exposes an HTTP endpoint. When `test_rwa_tokenization.py` sends a request, the Oracle checks the XRPL DID's simulated KYC status and, if approved, calls the `updateKYCStatus` function on the `GCBToken.sol` contract to whitelist the corresponding EVM address. This action simulates the cross-chain data flow enabled by Axelar.

## Technologies Used

* **Languages:** Python, Solidity
* **Python Libraries:**
    * `xrpl-py`: For XRPL wallet generation and interaction.
    * `web3.py`: For interacting with the XRPL EVM Sidechain (contract deployment, calls, transactions).
    * `solcx`: For compiling Solidity contracts directly in Python.
    * `Flask`: For building the light-weight HTTP server for the KYC Oracle.
    * `python-dotenv`: For managing environment variables securely.
    * `requests`: For making HTTP requests (e.g., from the test script to the oracle).
* **Solidity Libraries:** OpenZeppelin Contracts (for robust ERC-20 implementation).
* **Blockchain Networks:** XRPL DevNet/Testnet, XRPL EVM Sidechain DevNet/Testnet.

## Setup Instructions

**Prerequisites:**

* Python (v3.9+)
* `pip` (Python package installer)
* Git

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/xrpl-evm-did-prototype-py.git](https://github.com/your-username/xrpl-evm-did-prototype-py.git) # Replace with your repo
    cd xrpl-evm-did-prototype-py
    ```

2.  **Create and activate a Python virtual environment (highly recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Solidity Compiler (`solc`):**
    The `solcx` Python library will attempt to install `solc` automatically the first time it runs. If you encounter issues, you might need to install `solc` manually via your system's package manager.
    * On Ubuntu: `sudo apt-get install solc`
    * On macOS (Homebrew): `brew install solidity`

5.  **Configure Environment Variables (`.env`):**
    Create a file named `.env` in the root of your project and populate it with your testnet details. **These are testnet keys and should NEVER be used for real funds.**

    * **`XRPL_NETWORK_URL`**: Use `wss://s.devnet.rippletest.net:51233` or `wss://s.altnet.rippletest.net:51233` (Testnet).
    * **`XRPL_MASTER_ACCOUNT_SEED`**: (Optional) To get a testnet account with funds, visit [XRPL Testnet Faucet](https://xrpl.org/xrp-testnet-faucet.html) or [XRPL DevNet Faucet](https://xrpl.org/xrp-devnet-faucet.html). Copy the "Secret (Seed)" and paste it here if you prefer to fund wallets from a specific source instead of the faucet. `xrpl_did_kyc_setup.py` uses the faucet by default.
    * **`EVM_NETWORK_URL`**: Use `https://rpc-evm-sidechain.xrpl.org` for the XRPL EVM Sidechain Devnet.
    * **`EVM_DEPLOYER_PRIVATE_KEY`**: This will be the account that deploys the `GCBToken` contract and acts as the "GCB Owner" or "Issuer" for initial token distribution. It also acts as the "Oracle" in this simplified prototype. **You MUST fund this address with test XRP for gas on the XRPL EVM Sidechain.** Visit [XRPL EVM Sidechain Faucet](https://xrpl.org/xrp-evm-sidechain-faucet.html) to fund your address. Generate a new private key for testing purposes.
    * **`ACCESS_CONTROL_CONTRACT_ADDRESS`**: This will be filled automatically by the `deploy_gcb_token.py` script after successful deployment. Keep it empty initially.
    * **`ORACLE_PORT`**: The port for the Flask oracle server (e.g., `3000`).

    Example `.env` file:
    ```
    # .env
    XRPL_NETWORK_URL=wss://s.devnet.rippletest.net:51233
    # XRPL_MASTER_ACCOUNT_SEED=sEdV4LdYdMhR1z89Yv2jQp7oXn6mP3k5 # Optional, uncomment if using
    EVM_NETWORK_URL=[https://rpc-evm-sidechain.xrpl.org](https://rpc-evm-sidechain.xrpl.org)
    EVM_DEPLOYER_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bac478cbfd5c6439e0da1609756bde0 # REPLACE with your testnet private key
    ACCESS_CONTROL_CONTRACT_ADDRESS= # This will be set automatically after deployment
    ORACLE_PORT=3000
    ```

6.  **Download OpenZeppelin Contracts (for Solidity compilation):**
    `solcx` needs to resolve imports like `@openzeppelin/contracts`. The simplest way to achieve this for this prototype is to install `openzeppelin-contracts` via npm, even if your main project is Python:
    ```bash
    npm install @openzeppelin/contracts # Run this in your project root
    ```
    This will create a `node_modules` folder that `solcx` can find.

## Running the Prototype

You will need to run the scripts in a specific order, as they depend on each other. Open **three separate terminal windows** for these steps.

1.  **Terminal 1: Setup XRPL DID & KYC Data**
    This script will generate multiple XRPL testnet wallets and simulate their KYC status, saving the data to `gcb_kyc_data.json`.
    ```bash
    cd did-x-prototype-py
    source venv/bin/activate # Activate virtual environment
    python scripts/xrpl_did_kyc_setup.py
    ```
    * **Output:** Observe the generated XRPL Wallet Addresses, DIDs, and simulated KYC statuses. A `gcb_kyc_data.json` file will be created in your project root.

2.  **Terminal 2: Deploy EVM GCB Token Contract**
    This script will compile `GCBToken.sol` and deploy it to the XRPL EVM Sidechain. It will then update your `.env` file with the deployed contract address.
    ```bash
    cd did-x-prototype-py
    source venv/bin/activate # Activate virtual environment
    python scripts/deploy_gcb_token.py
    ```
    * **Output:** The `GCBToken deployed to: 0x...` address will be printed and automatically added to your `.env` file. **Verify that `ACCESS_CONTROL_CONTRACT_ADDRESS` in your `.env` file is now populated.**

3.  **Terminal 3: Start the GCB KYC Oracle**
    This script will start a Flask-based HTTP server that acts as our KYC oracle. It will load the simulated KYC data from `gcb_kyc_data.json` and listen for attestation requests.
    **Keep this running in this terminal window.**
    ```bash
    cd did-x-prototype-py
    source venv/bin/activate # Activate virtual environment
    python scripts/gcb_kyc_oracle.py
    ```
    * **Output:** You should see messages indicating the oracle is running and listening on `http://localhost:3000` (or your configured port).

4.  **Terminal 1 (Re-use): Test RWA Tokenization Flow**
    This script simulates investor actions (linking EVM address to XRPL DID, requesting KYC attestation) and tests token transfers based on whitelisting. It also simulates income distribution.
    ```bash
    cd did-x-prototype-py
    source venv/bin/activate # Activate virtual environment
    python scripts/test_rwa_tokenization.py
    ```
    * **Important:** This script will use the `gcb_kyc_data.json` file and the `ACCESS_CONTROL_CONTRACT_ADDRESS` from your `.env`. Ensure previous steps were successful.
    * **Output:** Carefully observe the console output in both this terminal and the Oracle terminal (Terminal 3). You should see:
        * Simulated investor EVM address generation and linking.
        * KYC attestation requests sent to the Oracle.
        * Oracle processing these requests and sending transactions to the EVM Sidechain to update whitelist status.
        * Verification of whitelisted status for each investor on the `GCBToken` contract.
        * Initial token allocation from the GCB Owner to whitelisted investors.
        * **Crucially:** Successful token transfers between *whitelisted* investors.
        * **Crucially:** Failed token transfers to *non-whitelisted* investors, demonstrating the access control.
        * The simulated `Income distribution initiated successfully` message and transaction hash.

## Verification & Expected Output

* **`xrpl_did_kyc_setup.py`:**
    * Generates `N` XRPL Wallets, DIDs, and assigns random `kyc_approved` statuses.
    * Creates `gcb_kyc_data.json` with this information.
* **`deploy_gcb_token.py`:**
    * Confirms connection to EVM network.
    * Prints the deployed `GCBToken` contract address.
    * Updates your `.env` file with `ACCESS_CONTROL_CONTRACT_ADDRESS`.
* **`gcb_kyc_oracle.py`:**
    * Confirms connection to EVM network and `GCBToken` contract.
    * Indicates it's running on `http://localhost:3000`.
    * When `test_rwa_tokenization.py` sends requests, you'll see messages about `KYC attestation request received`, `KYC Status: APPROVED/NOT APPROVED`, and `KYC status updated on GCBToken contract` with transaction hashes.
* **`test_rwa_tokenization.py`:**
    * Confirms connection to EVM network and `GCBToken` contract.
    * For each investor, it shows the process of requesting KYC attestation from the Oracle.
    * Prints the whitelisted status of each investor on the `GCBToken` contract, matching their simulated KYC status.
    * Shows initial token allocation to whitelisted investors.
    * Demonstrates successful token transfers between whitelisted investors.
    * **Demonstrates failed token transfers to non-whitelisted investors, displaying the "Sender not whitelisted" or "Recipient not whitelisted" error.** This is a key success metric.
    * Confirms `Income distribution initiated successfully` with a transaction hash.

You can verify transactions on the respective block explorers (e.g., [XRPL DevNet Explorer](https://devnet.xrpl.org/transactions/), [XRPL EVM Sidechain Explorer](https://evm-sidechain.xrpl.org/)) using the transaction hashes provided in the console output.

## Limitations and Future Work

* **Real-World Integration:** This is a prototype. A production RWA tokenization system would require:
    * **Legal Framework:** Robust legal agreements linking the tokens to the physical asset.
    * **Off-chain Identity:** Integration with actual KYC/AML providers.
    * **Custody:** Secure custody solutions for the underlying asset.
* **Axelar Integration:** The Axelar integration is simulated via a direct HTTP call to a local oracle. A full implementation would use Axelar's actual GMP SDKs and require monitoring Axelar's gateway for incoming cross-chain messages.
* **DID/VC Standards:** While `did:xrpl` is used, a full system would adhere to W3C Verifiable Credentials (VC) standards for issuing and verifying credentials cryptographically.
* **Oracle Decentralization:** The current oracle is centralized. In production, this could be a network of decentralized oracles or a more sophisticated cross-chain messaging protocol with higher security guarantees.
* **Income Distribution:** The `distributeIncome` function is simplified. For many token holders, a gas-efficient "pull" mechanism (where holders claim their share) or a Merkle tree-based distribution is more suitable.
* **EVM Investor Wallets:** For simplicity, the `test_rwa_tokenization.py` script assigns simple EVM addresses. In a real-world scenario, each investor would use their own securely managed EVM wallet.

This Python-based prototype robustly demonstrates the tokenization of a GCB with on-chain KYC enforcement and simulated earnings distribution, hitting all the requirements of "Question 2" effectively.

Sources
1. https://forum.openzeppelin.com/t/identifier-not-found-or-not-unique/37736
2. https://github.com/affresco/UNIGE_CAS_2021
3. https://github.com/lexarudev/NFT_marketplace_Backend
4. https://github.com/plotJ/raydiumswaps
5. https://github.com/tellor-io/timestamps-tip-scanner
6. https://github.com/alexindev/arbswap_airdrop_claimer
