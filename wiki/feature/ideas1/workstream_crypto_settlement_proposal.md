# Workstream 5: Crypto Settlement - Proposal and Agreement (Backend)

This workstream kicks off Phase 2, focusing on the backend infrastructure for users to propose, negotiate, and agree upon cryptocurrency-based settlements. Smart contract interaction itself is a subsequent workstream.

## Objectives:

*   Enable users to propose settling a fiat debt (derived from expense shares) with cryptocurrency.
*   Allow proposal of fixed exchange rates or agreement to use a dynamic oracle rate.
*   Facilitate creditor review, acceptance, rejection, or counter-proposal of these terms.
*   Store the agreed-upon settlement terms securely.

## Detailed Tasks:

1.  **Define Models and Schemas for Crypto Settlement Proposals:**
    *   **Backend (`app/src/models/models.py` and `app/src/models/schemas.py`):**
        *   **New Model: `CryptoSettlementProposal`**
            *   `id: Optional[int]`
            *   `proposer_user_id: int` (Foreign Key to User - the Debtor)
            *   `creditor_user_id: int` (Foreign Key to User)
            *   `expense_participant_id: int` (Foreign Key to `ExpenseParticipant` - the specific debt being settled). Could also be a list if settling multiple debts at once. For simplicity, start with one.
            *   `original_debt_amount: float` (e.g., 100 USD)
            *   `original_debt_currency_id: int` (e.g., USD)
            *   `proposed_settlement_crypto_currency_id: int` (Foreign Key to `Currency` - e.g., ETH, USDC)
            *   `proposed_settlement_crypto_amount: Optional[float]` (Amount of crypto offered, e.g., 0.05 ETH. Optional if rate is dynamic and amount is calculated at execution).
            *   `exchange_rate_type: str` (Enum: "fixed", "dynamic_oracle")
            *   `proposed_fixed_exchange_rate: Optional[float]` (e.g., 2000 USD/ETH. Required if `exchange_rate_type` is "fixed")
            *   `oracle_id: Optional[str]` (Identifier for the oracle if `exchange_rate_type` is "dynamic_oracle". E.g., "CHAINLINK_ETH_USD")
            *   `status: str` (Enum: "proposed", "accepted", "rejected", "countered", "expired", "executed", "failed")
            *   `created_at: datetime`
            *   `expires_at: Optional[datetime]` (Proposals could have an expiry)
            *   `last_updated_at: datetime`
            *   `counter_proposal_to_id: Optional[int]` (Self-referential FK for counter-proposals)
            *   `accepted_terms_snapshot: Optional[JSON]` (To store a snapshot of the exact terms when accepted, in case underlying parameters change)
        *   **Relationships:**
            *   Link to `User` (proposer, creditor), `ExpenseParticipant`, `Currency`.
        *   **Schemas:**
            *   `CryptoSettlementProposalCreate`
            *   `CryptoSettlementProposalRead`
            *   `CryptoSettlementProposalUpdate` (for status changes, counter-proposals)

2.  **API Endpoints for Proposal Management:**
    *   **Backend (`app/src/routers/crypto_settlements.py` - new router):**
        *   `POST /crypto-settlement-proposals/`: **Create Proposal**
            *   Input: `CryptoSettlementProposalCreate`.
            *   Action: Debtor (current_user) creates a proposal to settle a debt with a Creditor.
            *   Validate that the `proposer_user_id` actually owes the `creditor_user_id` for the specified `expense_participant_id` (use balance calculation logic).
            *   Store the new proposal with "proposed" status.
            *   Trigger notification to Creditor.
        *   `GET /crypto-settlement-proposals/`: **List Proposals**
            *   Query params: `user_role` ("proposer" or "creditor"), `status`.
            *   Returns a list of `CryptoSettlementProposalRead` relevant to the `current_user`.
        *   `GET /crypto-settlement-proposals/{proposal_id}`: **Get Proposal Details**
            *   Returns `CryptoSettlementProposalRead`.
            *   Auth: Proposer or Creditor.
        *   `POST /crypto-settlement-proposals/{proposal_id}/accept`: **Accept Proposal**
            *   Action: Creditor (current_user) accepts.
            *   Update proposal `status` to "accepted".
            *   Store `accepted_terms_snapshot`.
            *   Trigger notification to Proposer.
            *   (Further actions like smart contract deployment will be in a later workstream).
        *   `POST /crypto-settlement-proposals/{proposal_id}/reject`: **Reject Proposal**
            *   Action: Creditor (current_user) rejects.
            *   Update proposal `status` to "rejected".
            *   Trigger notification to Proposer.
        *   `POST /crypto-settlement-proposals/{proposal_id}/counter`: **Make Counter-Proposal**
            *   Input: `CryptoSettlementProposalCreate` (some fields pre-filled or adjusted).
            *   Action: Creditor (current_user) makes a counter.
            *   Original proposal `status` becomes "countered".
            *   New proposal created, linked via `counter_proposal_to_id`.
            *   Trigger notification to original Proposer (now the recipient of the counter).

3.  **Currency and Oracle Integration (High-Level):**
    *   **Backend:**
        *   Ensure `Currency` model can represent cryptocurrencies (e.g., add `is_crypto: bool` flag or a `type` field).
        *   For `dynamic_oracle` rates, a system to map `oracle_id` to actual oracle services (e.g., Chainlink feeds) will be needed. This is more for the execution phase but needs to be planned for in the model. For this workstream, storing the identifier is sufficient.

4.  **Notifications:**
    *   **Backend:**
        *   Integrate with Notification System (Workstream 8).
        *   Trigger notifications for:
            *   New proposal received.
            *   Proposal accepted, rejected, countered, or expired.

## Schema Changes Summary:

*   **`models.Currency`:**
    *   Potentially add `currency_type: str` (e.g., "fiat", "crypto") or `is_crypto: bool`.
*   **New Model `models.CryptoSettlementProposal`** (as detailed above).
*   **New Schemas `schemas.CryptoSettlementProposalCreate/Read/Update`**.

## API Endpoint Summary (New Router: `/crypto-settlement-proposals`):

*   `POST /`: Create a new crypto settlement proposal.
*   `GET /`: List proposals for the current user (as proposer or creditor).
*   `GET /{proposal_id}`: Get details of a specific proposal.
*   `POST /{proposal_id}/accept`: Accept a proposal.
*   `POST /{proposal_id}/reject`: Reject a proposal.
*   `POST /{proposal_id}/counter`: Make a counter-proposal.

## Key Considerations:

*   **Security:** Ensure only authorized users (proposer, creditor) can act on proposals.
*   **Clarity of Terms:** The `accepted_terms_snapshot` is crucial to lock in the agreement details, especially if oracles or amounts might be calculated dynamically later.
*   **Debt Validation:** Before a proposal can be made, the system must verify that the underlying fiat debt (from `ExpenseParticipant`) actually exists and is outstanding between the proposer and creditor. This links back to the Balance Calculation workstream.
*   **Proposal Expiry:** Implementing an expiry mechanism for proposals is good practice.

## Out of Scope for this Workstream:

*   Actual smart contract interaction (deployment, execution).
*   Wallet integration.
*   Real-time oracle data fetching (only storing configuration/identifiers for now).
*   Updating `ExpenseParticipant` status upon proposal acceptance (this happens after successful execution).

---
This workstream lays the critical groundwork for enabling crypto settlements by establishing how users agree on the terms. It focuses on the off-chain logic of proposal and agreement.
