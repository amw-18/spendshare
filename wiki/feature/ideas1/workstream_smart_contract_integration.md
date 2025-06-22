# Workstream 7: Smart Contract Integration for Crypto Settlement

This workstream focuses on defining, developing, and integrating smart contracts to facilitate more advanced crypto settlement features, such as escrow or oracle-based exchange rates, as mentioned in `ideas1.md`.

## Objectives:

*   Define the specific requirements and functionalities for smart contracts in the settlement process.
*   Develop, test, and deploy these smart contracts on relevant blockchain(s).
*   Build backend services to interact with these smart contracts (e.g., to initiate an escrow, trigger a payout, read contract state).

## Detailed Tasks:

1.  **Define Smart Contract Requirements & Scope:**
    *   **System Design:**
        *   Based on `ideas1.md`, smart contracts could be used for:
            *   **Escrow:** Debtor sends funds to a contract, Creditor confirms receipt (or other conditions met), contract releases funds. This adds a layer of trust.
            *   **Fixed Exchange Rate Enforcement:** Contract is encoded with the agreed fixed rate.
            *   **Dynamic Oracle Rate Usage:** Contract integrates with an oracle (e.g., Chainlink) to get the spot rate at the time of execution.
        *   **Initial Scope:** Determine the *minimum viable smart contract functionality*. A full escrow with oracle integration is complex.
            *   **Option A (Simpler):** A contract that primarily helps enforce a fixed exchange rate for a direct transfer, or acts as a very simple "conditional payment" mechanism.
            *   **Option B (More Complex):** A full escrow contract where funds are held until specific conditions are met, potentially with dispute resolution (though dispute resolution is likely out of scope for an MVP).
        *   **Decision:** Focus initially on a smart contract that can facilitate a settlement with a **fixed exchange rate** or use a **pre-agreed oracle feed for a dynamic rate at execution**. True "escrow" where the contract holds funds for an extended period before conditions are met by the creditor might be a later enhancement. The contract would ensure the correct amount is transferred based on the agreed rate type.

2.  **Smart Contract Development (e.g., using Solidity for EVM chains):**
    *   **Contract Logic:**
        *   `initialize_settlement(debtor, creditor, fiat_amount, fiat_currency, crypto_currency, rate_type, fixed_rate_value, oracle_feed_address)`: Called by the backend (or a user with specific data) to set up the terms.
        *   `deposit_funds()`: Called by the Debtor to send crypto to the contract. Contract verifies the amount if rate is fixed, or prepares for dynamic rate.
        *   `execute_settlement()`:
            *   If fixed rate: Transfers deposited funds to Creditor.
            *   If dynamic rate: Queries oracle, calculates crypto amount based on `fiat_amount`, ensures deposit covers it, then transfers to Creditor. Refunds excess to Debtor.
        *   `claim_refund()`: For Debtor if they over-deposited or if settlement is cancelled before execution.
        *   Events for all major state changes (e.g., `SettlementInitialized`, `FundsDeposited`, `SettlementExecuted`, `RefundClaimed`).
    *   **Security:** Follow smart contract security best practices (e.g., checks-effects-interactions, reentrancy guards, proper access control).
    *   **Testability:** Write comprehensive unit tests (e.g., using Hardhat/Foundry).

3.  **Smart Contract Deployment:**
    *   **Backend/DevOps:**
        *   Deploy contracts to testnets (e.g., Sepolia, Goerli) and eventually mainnet(s).
        *   Manage contract addresses and ABIs. The backend will need these to interact with the deployed contracts. Store them securely in configuration.

4.  **Backend Services for Smart Contract Interaction:**
    *   **Backend (`app/src/services/smart_contract_service.py` - new service):**
        *   Functions to interact with the deployed smart contracts:
            *   `prepare_contract_settlement_data(proposal: CryptoSettlementProposal) -> Tuple[str, str]`: Generates the contract address and encoded function call data for the frontend to use when the Debtor initiates the deposit into the smart contract. This would be called by the `/execution-details` endpoint from Workstream 6 if a smart contract pathway is chosen for the settlement.
            *   The `deposit_funds()` call would be made by the Debtor via their wallet, using data from above.
            *   `trigger_oracle_settlement(proposal: CryptoSettlementProposal)`: If the contract requires an external trigger to poll an oracle and finalize (some designs might have the user trigger this).
            *   `get_contract_settlement_status(proposal: CryptoSettlementProposal)`: Read status from the contract.
        *   These functions will use libraries like `web3.py` (for Python) to interact with the blockchain.
        *   The `BlockchainMonitorService` (from Workstream 6) would monitor for events emitted by these smart contracts to confirm deposit, execution, etc., then update the app's database.

5.  **Integration with Proposal and Execution Flow:**
    *   **Backend:**
        *   Modify `CryptoSettlementProposal` to store `smart_contract_address: Optional[str]` and `settlement_pathway: str` (e.g., "direct_transfer", "smart_contract_escrow").
        *   If `settlement_pathway` is "smart_contract_escrow":
            *   The `/execution-details` endpoint (Workstream 6) would provide data for the Debtor to call the smart contract's `deposit_funds` function.
            *   The `BlockchainMonitorService` would listen for contract events (e.g., `FundsDeposited`, `SettlementExecuted`) instead of just a direct transfer confirmation.
            *   The `CryptoSettlementProposal.status` would reflect contract states (e.g., "pending_contract_deposit", "funds_in_contract", "contract_executed").

## Schema Changes Summary:

*   **`models.CryptoSettlementProposal`:**
    *   Add `smart_contract_address: Optional[str] = Field(default=None, nullable=True)`.
    *   Add `settlement_pathway: Optional[str] = Field(default="direct_transfer")` (e.g., "direct_transfer", "smart_contract_fixed_rate", "smart_contract_oracle_rate").
    *   Add `contract_interaction_data: Optional[JSON]` (to store any specific data related to the contract instance for this proposal, like internal IDs or states).
*   Configuration management for deployed contract addresses and ABIs.

## API Endpoint Changes/Additions:

*   The `/crypto-settlement-proposals/{proposal_id}/execution-details` endpoint (from Workstream 6) will need to be enhanced. If the proposal indicates a smart contract pathway, it should return the contract address and the encoded calldata for the user's wallet to interact with the smart contract (e.g., to call `deposit_funds()`).

## Key Considerations:

*   **Complexity & Cost:** Smart contracts add significant complexity and gas costs. Start with the simplest contract that adds value.
*   **Security Audits:** Any smart contract handling real funds MUST undergo rigorous security audits. This is a major step before mainnet deployment.
*   **Upgradability:** Consider proxy patterns or other upgradability mechanisms for smart contracts if future changes are anticipated, though this adds complexity.
*   **Oracle Reliability & Costs:** If using oracles, depend on reputable ones. Oracle calls can also incur costs.
*   **Supported Blockchains:** Decide which blockchain(s) to support initially. Each may require separate contract deployments and backend configurations.

## Out of Scope for this Workstream:

*   Full dispute resolution mechanisms within smart contracts.
*   Frontend components for interacting with smart contracts (though backend provides data for it).
*   Security audits (this is a separate, critical process post-development).

---
This workstream is highly technical and introduces on-chain logic to the settlement process. It requires careful design, development, and testing due to the immutable nature of smart contracts and the financial assets involved.
