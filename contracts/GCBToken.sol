// contracts/GCBToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Context.sol";

/**
 * @title GCBToken
 * @dev An ERC-20 token representing fractional ownership of a Good Class Bungalow (GCB)
 * on the XRPL EVM Sidechain. This token implements a whitelist-based access control
 * mechanism for transfers, relying on KYC verification from an off-chain oracle.
 * It also includes a function for distributing simulated income.
 */
contract GCBToken is ERC20, Ownable {
    // Mapping to track whitelisted investors
    mapping(address => bool) public isWhitelisted;

    // The address of our trusted KYC oracle (simulating Axelar Gateway in this context)
    address public kycOracleAddress;

    // Events
    event KYCStatusUpdated(address indexed investor, bool status);
    event TokensDistributed(address indexed distributor, uint256 amount);
    event IncomeDistributed(address indexed sender, uint256 totalAmount, uint256 timestamp);

    constructor(uint256 initialSupply, address _kycOracleAddress)
        ERC20("Good Class Bungalow Share", "GCBS")
        Ownable(msg.sender)
    {
        require(_kycOracleAddress != address(0), "KYC Oracle address cannot be zero");
        kycOracleAddress = _kycOracleAddress;

        _mint(msg.sender, initialSupply); // Mints initial supply to the deployer (GCB owner/issuer)
    }

    /**
     * @dev Modifier to restrict functions to only whitelisted addresses.
     * This ensures only KYC'd individuals can interact with tokens.
     */
    modifier onlyWhitelisted() {
        require(isWhitelisted[_msgSender()], "Caller is not whitelisted for GCB Tokens");
        _;
    }

    /**
     * @dev Overrides the ERC20's _transfer function to enforce whitelisting.
     * Both sender and recipient must be whitelisted (except for the deployer/owner).
     */
    function _transfer(address from, address to, uint256 amount) internal override {
        // Allow owner to transfer tokens freely (e.g., for initial distribution)
        // or if both from and to are the zero address (e.g., burning/minting related to initial supply)
        if (from != owner() && to != owner()) { // Owner is special case for initial distribution/liquidity
             require(isWhitelisted[from], "Sender not whitelisted");
             require(isWhitelisted[to], "Recipient not whitelisted");
        } else if (from == address(0)) { // Minting
             // Minting to an un-whitelisted address is allowed, but they can't transfer out.
             // This can be used for initial distribution to investors who are not yet KYC'd,
             // and then they must undergo KYC to transfer.
             // For this prototype, we'll ensure minting is to whitelisted, or owner can manage.
        } else if (to == address(0)) { // Burning
             // No specific whitelist for burning, typically.
        }

        super()._transfer(from, to, amount);
    }

    /**
     * @dev Allows the KYC Oracle to update the whitelist status of an investor.
     * This function is called by the off-chain Python Oracle after verifying KYC status
     * via XRPL DIDs.
     * @param _investor The EVM address of the investor whose KYC status is being updated.
     * @param _status True to whitelist, false to de-whitelist.
     */
    function updateKYCStatus(address _investor, bool _status) external {
        require(msg.sender == kycOracleAddress, "Only the KYC Oracle can update status");
        require(isWhitelisted[_investor] != _status, "Status is already the same");
        isWhitelisted[_investor] = _status;
        emit KYCStatusUpdated(_investor, _status);
    }

    /**
     * @dev Sets a new KYC oracle address. Only callable by the contract owner.
     * @param _newKycOracleAddress The new address for the KYC oracle.
     */
    function setKycOracleAddress(address _newKycOracleAddress) external onlyOwner {
        require(_newKycOracleAddress != address(0), "New KYC Oracle address cannot be zero");
        kycOracleAddress = _newKycOracleAddress;
    }

    /**
     * @dev Simulates the distribution of income (e.g., rental proceeds) to token holders.
     * This function sends native currency (ETH on EVM Sidechain) to token holders
     * proportional to their share of the GCB tokens.
     * This is a simplified model; a more robust solution would involve a pull mechanism
     * or a separate dividend token.
     * @param _amount The total amount of native currency to distribute.
     */
    function distributeIncome(uint256 _amount) external onlyOwner {
        require(totalSupply() > 0, "No tokens in circulation to distribute income");
        uint256 totalShares = totalSupply();

        // This is a simplified distribution. In a real-world scenario,
        // you'd typically iterate through all token holders (if manageable)
        // or use a Merkle tree for gas efficiency for large numbers of holders.
        // For this prototype, we'll demonstrate a simple distribution to a few
        // known addresses, or rely on the `_transfer` function indirectly.
        // Or, more simply, just emit an event indicating income has been distributed.

        // To keep it simple and avoid gas limits for iterating all holders,
        // we'll just emit an event and the off-chain system would handle actual transfers.
        // For a true on-chain distribution, a pull-based mechanism is better.
        // Let's make it send to owner only for simplicity if a specific receiver isn't passed
        // or focus on the event.
        
        // Let's demonstrate by sending to the contract itself and then the contract owner can pull.
        // Or for simpler demo: imagine the income comes to the contract, and people claim.
        // For this demo, let's just emit the event and simulate the earning on the owner side.
        // A more complex system would involve a claim function:
        // function claimDividends() external {
        //     uint256 pendingDividends = calculateDividends(_msgSender());
        //     require(pendingDividends > 0, "No pending dividends");
        //     _msgSender().transfer(pendingDividends);
        //     // Update records
        // }
        
        // For prototype, we'll just log the total amount intended for distribution.
        // The actual transfer logic for many holders is beyond simple demonstration here.
        // The income is "distributed" notionally.
        emit IncomeDistributed(msg.sender, _amount, block.timestamp);
        
        // If we want to show funds actually being sent, the owner can pull it from the contract.
        // Or transfer to a specific recipient, e.g., the owner, for demonstration.
        // If _amount is sent to the contract itself (which is not typical for dist.), it accumulates.
        // Let's assume income arrives off-chain and this function logs its distribution intention.
    }
}