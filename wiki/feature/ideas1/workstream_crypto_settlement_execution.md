# Workstream 6: Crypto Settlement - Execution & Wallet Integration (Backend)

This workstream deals with the backend aspects of executing an agreed-upon crypto settlement. This includes integrating with user wallets for transaction signing, monitoring blockchain transaction status, and updating the application's ledger upon confirmation. This workstream assumes a `CryptoSettlementProposal` has reached an "accepted" state.

## Objectives:

*   Facilitate the Debtor's interaction with their crypto wallet to sign and dispatch the settlement transaction.
*   Monitor the blockchain for transaction confirmation.
*   Securely update the application's internal ledger (e.g., `ExpenseParticipant` status, `CryptoSettlementProposal` status) once the transaction is confirmed.
*   Link the internal settlement record to the blockchain transaction ID.

## Detailed Tasks:

1.  **Research and Select Wallet Integration Strategy:**
    *   **Backend/System Design:**
        *   Common approaches:
            *   **WalletConnect:** A popular open protocol to connect mobile crypto wallets to DApps (and potentially backend systems, though typically client-side).
            *   **Direct Wallet Extensions (e.g., MetaMask):** Primarily browser-based, frontend interacts, then sends signed transaction or signature to backend.
            *   **Server-Side Wallet Management (Custodial/HSM):** Not suitable for user-controlled wallets as per `ideas1.md`.
        *   For user-initiated transactions from their own wallets, the backend's role is often to:
            1.  Prepare transaction parameters based on the accepted proposal (amount, recipient address, contract call data if interacting with a smart contract).
            2.  Provide these parameters to the frontend.
            3.  Frontend uses user's wallet (MetaMask, WalletConnect) to sign & send.
            4.  Frontend sends back the transaction hash (ID) to the backend.
            5.  Backend monitors this transaction hash.
        *   **Decision for this workstream:** Assume the frontend handles direct wallet interaction (signing). The backend will provide necessary data and receive the transaction hash.

2.  **API Endpoints for Transaction Initiation and Monitoring:**
    *   **Backend (`app/src/routers/crypto_settlements.py`):**
        *   `GET /crypto-settlement-proposals/{proposal_id}/execution-details`: **Get Transaction Parameters**
            *   Auth: Only the Debtor of the accepted proposal.
            *   Action:
                *   Retrieves the accepted `CryptoSettlementProposal`.
                *   Determines recipient address (Creditor's designated crypto address - needs to be stored).
                *   Calculates crypto amount (if based on dynamic oracle at execution time).
                *   If interacting with a smart contract (from Workstream 7), prepares the contract call data.
                *   Returns these parameters (e.g., `to_address`, `amount`, `data`, `chain_id`) for the frontend to use with the user's wallet.
        *   `POST /crypto-settlement-proposals/{proposal_id}/submit-transaction-hash`: **Submit Blockchain Tx Hash**
            *   Auth: Only the Debtor.
            *   Input: `transaction_hash: str`, `blockchain_network_id: str` (e.g., "ethereum_mainnet", "polygon_mainnet").
            *   Action:
                *   Stores the `transaction_hash` and `blockchain_network_id` against the `CryptoSettlementProposal`.
                *   Updates proposal `status` to "pending_blockchain_confirmation".
                *   Initiates monitoring of this transaction hash (see task 3).
                *   Trigger notification to Creditor that payment is initiated.

3.  **Blockchain Transaction Monitoring Service:**
    *   **Backend (`app/src/services/blockchain_monitor_service.py` - new service):**
        *   **Mechanism:**
            *   Periodically query a blockchain node/API (e.g., Infura, Alchemy, Etherscan API) for the status of transactions marked "pending_blockchain_confirmation".
            *   This can be a background task (e.g., Celery beat, FastAPI background task, or a separate cron job).
        *   **On Confirmation:**
            *   Once a transaction is confirmed (with sufficient block confirmations):
                *   Update `CryptoSettlementProposal.status` to "executed".
                *   Update related `ExpenseParticipant.settled_transaction_id` (linking to the proposal or a new internal transaction record) and `settled_amount_in_transaction_currency`.
                *   Update/Verify `Expense.is_settled` status.
                *   Store blockchain transaction details (e.g., block number, final gas fees if available) with the proposal.
                *   Trigger notification to both Debtor and Creditor of successful settlement.
        *   **On Failure:**
            *   If a transaction fails on-chain:
                *   Update `CryptoSettlementProposal.status` to "failed_on_chain".
                *   Trigger notification to Debtor (and possibly Creditor).
        *   **Configuration:** Store RPC URLs, API keys for blockchain interaction securely.

4.  **Storing Creditor Crypto Addresses:**
    *   **Backend:**
        *   The Creditor needs a way to specify their receiving address for different cryptocurrencies.
        *   **New Model: `UserCryptoAddress`**
            *   `user_id: int` (FK to User)
            *   `currency_id: int` (FK to Currency - for the crypto)
            *   `address: str`
            *   `chain_id: Optional[str]` (e.g., "eip155:1" for Ethereum Mainnet, if addresses can be multi-chain for same currency symbol like USDC)
            *   `is_default: bool`
        *   **API Endpoints (`app/src/routers/users.py` or a new one):**
            *   Endpoints for users to add/list/delete their crypto addresses.
        *   The `GET /execution-details` endpoint will fetch the Creditor's appropriate address from here.

5.  **Updating Application Ledger:**
    *   **Backend:**
        *   When settlement is confirmed by the `BlockchainMonitorService`:
            *   The `ExpenseParticipant` record corresponding to the settled debt needs to be updated:
                *   `settled_transaction_id` could point to the `CryptoSettlementProposal.id` or a new generic `SettlementRecord.id` if one is introduced.
                *   `settled_amount_in_transaction_currency` should be the actual crypto amount transferred.
                *   The original `share_amount` (in fiat) is now considered covered.
            *   The `Expense.is_settled` status should be re-evaluated.
            *   The `CryptoSettlementProposal` should store the `blockchain_transaction_hash` and its final `status` ("executed" or "failed").

## Schema Changes Summary:

*   **`models.CryptoSettlementProposal`:**
    *   Add `blockchain_transaction_hash: Optional[str]`.
    *   Add `blockchain_network_id: Optional[str]`.
    *   Add `creditor_receiving_address: Optional[str]` (snapshot at time of execution details).
*   **New Model `models.UserCryptoAddress`** (as detailed above).
*   **New Schemas `schemas.UserCryptoAddressCreate/Read`**.
*   **`models.ExpenseParticipant`:** Ensure `settled_transaction_id` can accommodate linking to the proposal or a generic settlement record.

## API Endpoint Summary Additions/Changes:

*   In `app/src/routers/crypto_settlements.py`:
    *   `GET /{proposal_id}/execution-details`: Get parameters for frontend to initiate transaction.
    *   `POST /{proposal_id}/submit-transaction-hash`: Debtor submits the blockchain tx hash.
*   New router/endpoints for managing `UserCryptoAddress`.

## Key Considerations:

*   **Security of Blockchain Interaction:** API keys for node services must be secure.
*   **Reliability of Monitoring:** The blockchain monitor must be robust. Consider retries, handling node downtime.
*   **Gas Fees:** Borne by the Debtor. The system records the transaction, doesn't pay gas.
*   **Finality:** Define what "confirmed" means (number of block confirmations).
*   **Oracle Usage for Dynamic Rates:** If a dynamic rate was agreed, the `GET /execution-details` endpoint (or the monitoring service just before execution if the smart contract handles it) would need to fetch this rate from the oracle. This is a critical step if not handled by a smart contract directly.

## Out of Scope for this Workstream:

*   Frontend wallet interaction code (MetaMask, WalletConnect integration).
*   Smart contract deployment/interaction logic (Workstream 7). This workstream assumes direct peer-to-peer crypto transfer or that the smart contract address and call data are prepared by Workstream 7 and provided via `/execution-details`.

---
This workstream connects the off-chain agreement to on-chain reality, handling the complexities of blockchain transaction submission and monitoring. It's a critical step for realizing crypto settlements.
